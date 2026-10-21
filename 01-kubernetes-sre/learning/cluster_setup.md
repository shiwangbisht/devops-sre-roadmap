# Kubernetes — cluster setup: self-managed vs. managed

Both, deliberately — self-managed (kubeadm) teaches you what's actually happening under a managed
cluster's hood; managed (EKS) teaches you the production operational reality most jobs actually run.
Doing only EKS means "AWS does it" is your whole mental model for control-plane HA, upgrades, and
etcd — doing only kubeadm means you never learn what AWS specifically takes off your plate and why
teams pay for that. Do both, in that order.

**Safety reminder — this provisions real, billable EC2/EKS resources:**
```bash
export AWS_SHARED_CREDENTIALS_FILE=~/.aws/credentials_terraform
aws sts get-caller-identity   # must show Account: 003720987974 — the learning account, never company
```
**Tear everything down at the end of each exercise** — a kubeadm 3-node EC2 cluster and an EKS cluster
both cost real money by the hour while running.

---

## Who manages what — the actual comparison

| Component | Self-managed (kubeadm) | Managed (EKS) |
|---|---|---|
| etcd | You run it, back it up, upgrade it | AWS runs it, multi-AZ, backed up automatically |
| API server | You run it, scale it, patch it, secure its certs | AWS runs it, HA across AZs, patched by AWS |
| Scheduler / controller-manager | You run it | AWS runs it |
| Control plane upgrades | You orchestrate, including etcd — the highest-risk operation in K8s ops | One-click/API-triggered, AWS handles the hard part |
| Worker nodes | You provision, bootstrap, join, patch | You provision (managed node groups, self-managed node groups, or Fargate) — still your responsibility either way |
| Networking (VPC CNI, LB integration) | You wire it all by hand | Native integration (ALB/NLB via annotations, VPC CNI pre-wired) |
| IAM integration | You build your own auth bridge | Native (`aws-auth` ConfigMap / EKS access entries map IAM → RBAC) |
| Cost | EC2 instances only, but your time is the real cost | Control plane: ~$0.10/hr flat + worker node EC2 cost |

**Interview-ready framing:** self-managed gives full control at the cost of owning every failure mode,
including the scariest one (etcd corruption/loss) yourself. Managed trades some control (you can't SSH
into the API server) for AWS owning control-plane availability and upgrade mechanics — which is almost
always the right trade for a team that isn't specifically in the business of running Kubernetes itself.

---

## Part 1 — Self-managed cluster with kubeadm (do this first)

**Plan:** 3 EC2 instances (1 control plane, 2 workers), Ubuntu, `t3.medium` (kubeadm needs ≥2 vCPU on
the control plane node), same VPC/subnet, security group allowing all traffic between them + SSH to you.

### Step 1 — Launch the EC2 instances (manual, console or CLI)
Launch 3 instances in the learning account: `k8s-control-plane`, `k8s-worker-1`, `k8s-worker-2`.
Same security group, opening at minimum: 22 (SSH, from your IP), 6443 (API server), 10250 (kubelet),
and all traffic between the instances themselves (simplest: allow all traffic within the SG).

### Step 2 — On every node: install containerd + kubeadm/kubelet/kubectl
```bash
sudo apt-get update && sudo apt-get install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd

sudo swapoff -a   # kubelet refuses to start with swap enabled

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update && sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl   # don't let unattended upgrades break version skew
```

### Step 3 — On the control plane node only: `kubeadm init`
```bash
sudo kubeadm init --pod-network-cidr=192.168.0.0/16   # CIDR must match whatever CNI you pick next

mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```
`kubeadm init` prints a `kubeadm join ...` command with a token — **copy it**, you need it for the
workers next. (Tokens expire after 24h — re-generate with `kubeadm token create --print-join-command`
if you come back later.)

### Step 4 — Install a CNI (cluster has no pod networking without one)
```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml
```
Nodes stay `NotReady` until a CNI is installed — this is the #1 "my cluster is broken" moment for
first-time kubeadm users, and it's not broken, it's just missing this step.

### Step 5 — On each worker node: join the cluster
```bash
sudo kubeadm join <control-plane-ip>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```
(The exact command was printed by `kubeadm init` in Step 3.)

### Step 6 — Verify
```bash
kubectl get nodes          # all 3 should show Ready once CNI is up
kubectl get pods -A        # control plane components running as pods in kube-system
```

### What to actually pay attention to while doing this
- `kubectl get pods -n kube-system` shows you the control plane components (`kube-apiserver`,
  `etcd`, `kube-scheduler`, `kube-controller-manager`) running as **static pods** — managed directly by
  the kubelet from manifest files in `/etc/kubernetes/manifests/`, not by the scheduler. Go look at that
  directory on the control plane node — this is the "how does the API server bootstrap before there's an
  API server to schedule it" answer, a genuinely good interview question.
- Try `sudo systemctl status kubelet` on a worker — kubelet is the one actual systemd service in all of
  this; everything else is a container the kubelet itself manages.

**Teardown:** terminate all 3 EC2 instances when done.

---

## Part 2 — Managed cluster with EKS

### Step 1 — Create the cluster (console)
EKS → Create cluster → name it, choose a Kubernetes version, choose/create a cluster IAM role (needs
`AmazonEKSClusterPolicy`), choose your VPC + at least 2 subnets in different AZs (EKS control plane
needs multi-AZ subnets even though you don't manage the control plane instances yourself).

### Step 2 — Add compute: compare the three options for real
- **Managed node group** — EC2 instances AWS provisions/patches/drains for you via an ASG;
  closest to self-managed workers but with lifecycle automation. Create one: pick instance type,
  min/max/desired size, a node IAM role (needs `AmazonEKSWorkerNodePolicy`,
  `AmazonEKS_CNI_Policy`, `AmazonEC2ContainerRegistryReadOnly`).
- **Self-managed node group** — you own the EC2 instances/ASG/launch template yourself, EKS just lets
  them join. Rarely worth it vs. managed node groups unless you need something a managed node group's
  limited customization doesn't allow.
- **Fargate profile** — no EC2 nodes at all; each pod gets its own micro-VM. No node-level
  patching/capacity planning, but no DaemonSets, no privileged pods, and per-pod pricing can cost more
  at steady, predictable load than right-sized EC2.

**Do a managed node group for this exercise** — it's the default real-world choice for most teams.

### Step 3 — Connect kubectl
```bash
aws eks update-kubeconfig --region us-east-1 --name <cluster-name>
kubectl get nodes
```
`update-kubeconfig` doesn't give you a static credential — it wires `kubectl` to call `aws eks
get-token` on every request, so your **existing IAM identity** (via `credentials_terraform`) *is* your
Kubernetes auth. This is the thing self-managed kubeadm doesn't give you for free — you'd have to build
an OIDC/webhook bridge yourself to get IAM-based auth there.

### Step 4 — Compare directly against Part 1
```bash
kubectl get pods -n kube-system     # notice: no etcd, no kube-apiserver, no kube-controller-manager pods here — AWS runs them outside your visibility entirely
```
This absence is the whole point of "managed" — go confirm it yourself rather than taking the README's
word for it.

**Teardown:** delete the node group, then the cluster (console, or `eksctl delete cluster` if you end
up using `eksctl` later) — EKS control plane bills hourly even idle.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What specifically does AWS take off your plate with EKS that you'd own yourself with kubeadm?* —
   etcd (backup, upgrade, multi-AZ HA), the API server/scheduler/controller-manager's own availability
   and patching, and control-plane upgrade orchestration — the components where a mistake has the
   widest blast radius and the steepest operational expertise requirement.
2. *A kubeadm cluster's nodes are stuck `NotReady` right after `kubeadm join`. What's almost certainly
   wrong?* — No CNI installed yet — pod networking doesn't exist until you apply one (Calico, Flannel,
   etc.); `kubeadm init`/`join` only sets up the control plane and node registration, not pod networking.
3. *How do control plane components actually start on a kubeadm control plane node, before there's a
   scheduler to schedule anything?* — They run as **static pods**, defined by manifest files in
   `/etc/kubernetes/manifests/` that the kubelet watches directly and runs without needing the API
   server/scheduler to exist first — this is how the system bootstraps itself.
4. *Managed node group vs. Fargate — when would you pick each?* — Managed node group for predictable,
   steady workloads (better cost at scale, supports DaemonSets/privileged pods); Fargate for spiky/
   unpredictable workloads or when you want zero node-level ops at the cost of per-pod pricing and losing
   DaemonSet/privileged-pod support.
5. *How does `aws eks update-kubeconfig` actually authenticate you to the cluster — is there a static
   credential involved?* — No — it configures `kubectl` to call `aws eks get-token` per request, so your
   existing IAM identity is the auth, mapped to Kubernetes RBAC via the `aws-auth` ConfigMap or EKS
   access entries. No separate Kubernetes-specific credential to manage/rotate.
6. *What's the highest-risk operation in a self-managed cluster that EKS removes almost entirely?* —
   etcd backup/restore and control-plane version upgrades (especially etcd's own upgrade) — the
   operations most likely to take the whole cluster down if done wrong, and the ones AWS fully owns in EKS.
7. *Why does kubeadm require swap to be disabled?* — The kubelet refuses to start with swap enabled by
   default — resource accounting (what the scheduler/kubelet assume about available memory) becomes
   unreliable when the kernel can swap memory out, which conflicts with how Kubernetes reasons about
   resource requests/limits.
8. *If a team is small and has no dedicated platform/infra function, which should they pick and why?* —
   Managed (EKS) — the operational cost of correctly running etcd/control-plane HA/upgrades yourself is
   real and ongoing; a small team is almost always better served paying AWS for that and spending their
   own time on the application layer.