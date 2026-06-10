---
name: feedback-copyable-items-standalone
description: "When Bill needs to copy a link, email, ID, or similar token, present it in its own plain code block — never embedded in prose."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bcefcd91-35dd-4c26-b825-89768073f856
---

# Copyable items go in their own code block

When Bill will need to copy something (URL, email address, ID, token, command, path, key, etc.), present it on its own line in a fenced code block with no surrounding prose inside the block. Lead-in text is fine outside the block.

**Why:** Embedding a copyable token inside a sentence or alongside other text makes it hard to select cleanly — terminals and chat UIs often grab adjacent characters or whitespace. Bill explicitly called this out 2026-06-02 when the SA email was offered inline and he had to ask for a "plain, standalone copyable" version.

**How to apply:** Any time the next user action is likely "copy this and paste it somewhere," isolate the copyable token. Example:

> Open Drive → Share → add this as Content manager:
> ```
> intake-email-reader@ipul-intake-system.iam.gserviceaccount.com
> ```

Applies to: email addresses, URLs, Drive/folder IDs, channel IDs, SHA hashes, file paths, one-liner commands, secrets references. If there are multiple items, give each its own block.
