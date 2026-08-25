# Documentum Connector -- Ideal Onboarding

## Goal
Get a user from "I have a Documentum repository" to "Webbee can browse/manage my content
and drive its lifecycles" in under two minutes.

## Step 1 -- What the user needs before connecting
- Their Documentum REST base URL, e.g. `https://dctm.acme.com:8080/dctm-rest`.
- The repository name (docbase name) they want to work in, e.g. `acme_prod`.
- A username + password with REST access to that repository.
No API key, no OAuth app registration -- Basic Auth against the repository is the universal
baseline, so onboarding is as fast as OTCS's.

## Step 2 -- Connecting (chat or sidebar form)
`connect_documentum(base_url, repository_name, username, password, label?)`:
1. Connector calls `GET {base_url}/repositories/{repository_name}` with Basic Auth.
2. On a 200, stores the four fields (password is required on every request -- Basic Auth
   has no token to cache, so there is no "expiry" to handle, unlike OTCS's ticket).
3. Friendly label defaults to `repository_name` if left blank.

## Step 3 -- First 60 seconds after connecting
Sidebar surfaces:
- A **Cabinets** shortcut -- lists the repository's top-level cabinets so the user has an
  entry point into the content tree without knowing any object IDs.
- An **Audit** shortcut (`audit_content_health`) -- checked-out-too-long documents, empty
  documents, missing lifecycles.

## Step 4 -- What could go wrong
- **Wrong repository name**: `GET /repositories/{name}` 404s; connector says plainly
  "Could not find a repository named '{name}' on this Content Server."
- **Wrong base_url**: connection refused/404 on the repositories list itself; connector
  says "Could not reach Documentum REST Services at this URL -- check it ends at .../dctm-rest
  (no trailing repository path)."
- **401 Unauthorized**: username/password rejected; connector surfaces this plainly rather
  than retrying blindly (Basic Auth has nothing to refresh).
- **Object checked out by someone else**: version/content-update calls fail with a locked-
  object error; connector surfaces "This document is checked out by {r_lock_owner} -- ask
  them to check it in, or use an admin account with override rights."

## Step 5 -- The killer feature: lifecycles
Unlike Box/SharePoint/OpenText (flat metadata only), Documentum sysobjects can be attached
to a state-machine Lifecycle. `get_lifecycle_state` / `promote_lifecycle` / `demote_lifecycle`
are first-class actions so users can literally say "move this contract to Approved" and have
it happen, instead of hand-editing a status field.
