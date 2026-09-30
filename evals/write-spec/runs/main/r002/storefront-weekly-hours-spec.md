# Implementation spec — Storefront weekly opening and closing hours

> Store the opening and closing hours of each storefront for every day of the week, using the existing hours-of-operation object.

_Based on the requirement, the evidence reported by AskCoworker, and read-only org queries where noted. Assumptions and missing evidence are identified below. Specification only — nothing is implemented or deployed._

---

## 1. The requirement

Each `Storefront__c` record needs one opening time and one closing time for each of the seven days of the week; the org already meets this with `Storefront_Hours_of_Operation__c`, so no metadata changes are required. No user decision changed the scope, and the request contained no deploy or data-change instruction.

| # | Responsibility | Trigger | Where it lives |
| --- | --- | --- | --- |
| 1 | Hold one hours record per storefront per day | Record insert or update | `Storefront_Hours_of_Operation__c` (existing) |
| 2 | Identify the day of the week | Record insert or update | `Storefront_Hours_of_Operation__c.Day_of_Week__c` (existing) |
| 3 | Hold the opening and closing times | Record insert or update | `Storefront_Hours_of_Operation__c.Opening_Time__c`, `Storefront_Hours_of_Operation__c.Closing_Time__c` (existing) |
| 4 | Create or update the hours for one storefront and day | Invocable action call | `AgentUpdateStorefrontHoursActions` (existing) |

## 2. Grounding — reuse before building

Target org: `TestWriteSpecDE` (connected). API version: `67.0`.

- **`Storefront__c`** (CustomObject) — the storefront object. Unmanaged (no namespace). It has no hours, opening, or closing fields of its own. 21 records. _verified by org query_
- **`Storefront_Hours_of_Operation__c`** (CustomObject) — the existing store for the hours. Unmanaged. Child relationship name on `Storefront__c` is `Storefronts__r`. _verified by org query_
- **`Storefront_Hours_of_Operation__c.Storefront__c`** (CustomField, Master-Detail to `Storefront__c`, cascade delete) — links each hours record to its storefront. _verified by org query_
- **`Storefront_Hours_of_Operation__c.Day_of_Week__c`** (CustomField, Picklist) — values `Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday`, `Saturday`, `Sunday`. _verified by org query_
- **`Storefront_Hours_of_Operation__c.Opening_Time__c`** and **`Storefront_Hours_of_Operation__c.Closing_Time__c`** (CustomField, Text(255)) — hold the times as text, for example `08:00 AM` and `10:00 PM`. _verified by org query_
- **`Storefront_Hours_of_Operation__c.Notes__c`** (CustomField, Text Area(255)) — free-text notes for a day. _verified by org query_
- **Data shape** — 147 hours records: 21 storefronts, 21 records for each of the 7 days, no duplicate storefront and day pairs, and no record with a blank opening or closing time. _verified by org query_
- **`AgentUpdateStorefrontHoursActions`** (ApexClass, `with sharing`, `@InvocableMethod` "Update Storefront Hours") — checks that the storefront belongs to the given Account, then updates the record for that storefront and day or creates it. It processes only the first request. It is the only metadata component that references the hours object. _verified by org query_
- **Automation** — no Apex triggers, no record-triggered flows, and no validation rules on `Storefront__c` or `Storefront_Hours_of_Operation__c`. _verified by org query_
- **Access** — `Agentforce_Reference_App` and `sfdc_accelerate_dms` grant Read, Create, Edit, and Delete on the hours object and Read and Edit on its fields; `sfdc_a360_sfcrm_data_extract` and `sfdc_slack` grant Read. _verified by org query_

Evidence sources: `sf org display`; `sf sobject describe` of both objects; Tooling queries on `EntityDefinition`, `ApexTrigger`, `ValidationRule`, `ApexClass`, and `MetadataComponentDependency`; standard queries on `FlowDefinitionView`, `ObjectPermissions`, `FieldPermissions`, and aggregate counts on the hours records. AskCoworker returned no citedReferences.

## 3. Architecture

```mermaid
flowchart LR
  a["AgentUpdateStorefrontHoursActions (existing)"] -->|"upserts one record per storefront and day"| h["Storefront_Hours_of_Operation__c (existing)"]
  h -->|"Master-Detail Storefront__c"| s["Storefront__c (existing)"]
```

Why the pieces are drawn this way:

1. `Storefront_Hours_of_Operation__c` is a Master-Detail child of `Storefront__c` through `Storefront_Hours_of_Operation__c.Storefront__c` (verified by org query).
2. `AgentUpdateStorefrontHoursActions` is the only component that references the hours object, and it writes the record for one storefront and day (verified by org query). Users with the object permissions listed in Section 2 can also write the records directly.
3. Nothing changes; every component is existing.

## 4. Metadata changes

No metadata changes are required.

## 5. Data 360 (Data Cloud) data involved

No Data 360 changes are needed. The Data Cloud connector permission set `sfdc_a360_sfcrm_data_extract` has Read access on `Storefront_Hours_of_Operation__c` and its fields (verified by org query), so the connector can read the records. Whether a data stream for this object is configured was not specified.

## 6. Security considerations

- **Execution context.** `AgentUpdateStorefrontHoursActions` runs `with sharing` and rejects a storefront that does not belong to the given Account (verified by org query).
- **Record sharing.** As a Master-Detail child, `Storefront_Hours_of_Operation__c` records inherit sharing from the parent `Storefront__c` record (reported by AskCoworker; standard Master-Detail behavior).
- **CRUD/FLS.** Read, Create, Edit, and Delete, plus Read and Edit on `Opening_Time__c`, `Closing_Time__c`, `Day_of_Week__c`, and `Notes__c`: `Agentforce_Reference_App`, `sfdc_accelerate_dms`. Read only: `sfdc_a360_sfcrm_data_extract`, `sfdc_slack`. Two profile-owned permission sets also have object access (verified by org query). Permission sets are not the only grant path; profiles and permission set groups can also grant access.
- **Permission set changes.** None.
- **Data exposure.** Opening and closing times are business information. No new exposure is introduced.

## 7. Testing strategy

No test components are in the inventory, and no tests were run. Recommended verification:

1. Call `AgentUpdateStorefrontHoursActions` for a storefront and day that already has a record; confirm the existing record is updated and no duplicate is created.
2. Call it for a storefront and day with no record; confirm one record is created.
3. Call it with a storefront that belongs to a different Account; confirm it returns `success = false`.
4. Call it with a blank day; confirm it returns `success = false`.
5. Run the aggregate check again: each storefront has exactly 7 records, one per `Day_of_Week__c` value.
6. As a user with only `sfdc_slack` or `sfdc_a360_sfcrm_data_extract`, confirm the hours can be read but not edited.

## 8. Open decisions

1. **Time format (non-blocking).** `Storefront_Hours_of_Operation__c.Opening_Time__c` and `Storefront_Hours_of_Operation__c.Closing_Time__c` are Text(255) with no format check, so any string is accepted. The Apex input descriptions say 24-hour `HH:MM`, but the stored data uses `08:00 AM` style, and at least one value (`5:00 PM`) has no leading zero (verified by org query). Recommended default: no change; a format validation rule is an optional enhancement.
2. **Uniqueness of storefront and day (non-blocking).** Only `AgentUpdateStorefrontHoursActions` prevents a second record for the same storefront and day; direct inserts do not. No duplicates exist today (verified by org query). Recommended default: no change.
3. **Closed days (non-blocking).** No field marks a day as closed; today every storefront has all 7 days populated (verified by org query). Recommended default: no change; use `Notes__c` or omit the record until the business asks for a closed flag.
4. **Test coverage for `AgentUpdateStorefrontHoursActions` (non-blocking).** No test class for it was found; the only storefront test class is `StorefrontPickerActionTest` (verified by org query). It is not needed for this requirement because nothing is deployed.
5. **`Pronto_Deep_Dive_Workshop` access (non-blocking).** This permission set reads `Storefront__c` but has no access to `Storefront_Hours_of_Operation__c` (verified by org query). The requirement did not ask for a grant, so least access applies: no change.
6. **Conflict: native Time type (non-blocking).** AskCoworker said Salesforce has no Time field type for custom fields. That is incorrect (assumption based on platform documentation; the org itself has Time fields such as `BusinessHours.MondayStartTime`, verified by org query). It does not change the inventory because the existing text fields meet the requirement.
7. **Conflict: cascade delete and the Recycle Bin (non-blocking).** AskCoworker said child hours records are hard-deleted when a `Storefront__c` is deleted and cannot be restored. Standard Master-Detail behavior is that the children go to the Recycle Bin with the parent and are restored when the parent is undeleted (assumption; not verifiable by read-only query). No change either way.
8. **Data stream (non-blocking).** Whether Data Cloud ingests `Storefront_Hours_of_Operation__c` was not specified. It does not affect this requirement.

## 9. Change set

| # | Action | Type | API name | Module | Why |
| --- | --- | --- | --- | --- | --- |

No metadata changes are required. The existing `Storefront_Hours_of_Operation__c` child of `Storefront__c` already stores one opening and closing time per storefront per day, written by `AgentUpdateStorefrontHoursActions`.

Total: 0 · Create: 0 · Update: 0 · Delete: 0
