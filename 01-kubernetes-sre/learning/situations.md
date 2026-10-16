# Kubernetes — situations (the "what do you actually say" doc)

Same idea as the Terraform one — a dev/PM asks for something mid-conversation, what do you actually say
and do, no time to go read docs.

---

### "Can you just bump the replica count manually for now, we're getting hammered?"

**What you say:** "I can `kubectl scale` it right now to stop the bleeding, but I'll set up HPA after so
this doesn't need a human watching it next time — manual scaling is a stopgap, not the fix."

### "The pod's crash-looping, can you just restart it?"

**What you say:** "A restart might clear the symptom but I want to check `kubectl logs --previous` and
`describe` first — if it's OOMKilled or a bad config, it'll just crash-loop again in a few minutes and
we'll be back here."

---

<!-- Add new situations as they come up in real work or practice. Template:

### "<what the dev/PM said, close to verbatim>"

**What you say:** <the actual words, not theory>

**What you actually do:** <the mechanics, if different from what you say>

-->
