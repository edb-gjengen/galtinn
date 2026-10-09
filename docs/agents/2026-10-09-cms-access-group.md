# CMS access group

## Goal

The CMS (cms.neuf.no, in the neuf-www repo) logs editors in through Galtinn's OIDC provider and grants access to members of one Galtinn group.
That group should be managed only by superusers in Django admin, not through the org unit pages.
This is an interim solution until access lifecycle is handled properly.

## What already worked

- The `groups` claim in `dusken/api/oauth_validators.py` carries the names of all the user's Django groups.
- The org unit pages and API only reach groups through `OrgUnit.group` and `OrgUnit.admin_group`, so a group no org unit points at is out of their reach.

So the group itself is plain data: a Django group with no `GroupProfile` and no org unit. It is created by hand in each environment and its name is not in the code.

## Changes

- `dusken/admin.py`: the stock group admin is replaced by `DuskenGroupAdmin`, which lists and edits members inline with a user autocomplete. Before, membership could only be edited from each user's page.
- `dusken/models/users.py`: `update_volunteer_status` now counts only groups tied to an org unit. Before, any extra group, such as the CMS group, kept a user in the volunteers group after they left their last org unit.
- `dusken/tests/test_cms_access_group.py`: the claim, the admin page, the org unit API leaving a standalone group alone, and the volunteer status cases.
- `README.md`: "Granting access by group" under the OIDC section.

## Behaviour change to be aware of

A user whose only groups besides volunteers are not tied to an org unit loses volunteer status the next time they are added to or removed from an org unit.
The old code also added a user to volunteers on removal from an org unit if they were in no groups at all; that no longer happens.

## Verification

- `uv run pytest`
- `prek run`
