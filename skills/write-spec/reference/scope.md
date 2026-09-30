# Scope: ask about intent, decide implementation (step 5)

Before drafting any question, predict the answer. If you expect "no preference" because your default is safe and reversible, decide instead. Two exceptions are always asked: choices with health, money, or legal consequences, and choices where the in-org candidates for a persona, channel, or recipient are different audiences (for example external contacts versus internal owners).

## Decide, with no question

Record each decision as an *assumption* in Section 8 "Resolved".

- *How* to build it: data structure (including how to represent a new entity, unless that changes who the users are), flow or trigger, API names, labels, placement, and message content.
- Naming differences with existing values: keep what exists.
- Backfills: list them as data steps.
- Follow-on changes to other components that the requirement does not need: list them as proposals.
- Enforcement strength: use the standard access control. Stronger guards are proposals.
- A choice between an in-org candidate that is used and one that has no data and no references, when your recommendation rests on implementation effort: take the used one.
- Any intent that the requirement's wording or the org's semantics answers: field descriptions, data shape, or a picklist value that matches the requirement's words (for example "New Business" for "new merchant").

## Ask

Ask only about *what the user wants*, when a wrong guess would change the inventory and the evidence gives no answer or points both ways:

- Missing business values (thresholds, amounts, dates), or a data convention that nothing settles (for example the sign of a points value).
- A requirement that contradicts itself. One that reconciles into a conditional rule, such as "required except for X", is decided.
- Which platform, channel, persona, or same-label field is meant. Once a platform or destination is named, how to connect or deliver to it (for example CDC versus a callout) is implementation.
- An ambiguous set of components to delete. An exact label or API-name match to a single component settles it; a keyword-only match does not. When a match settles it, record in Section 8 "Resolved" the evidence for each rejected candidate (label, record count, references), so a reviewer can catch a wrong pick.
- An environment fact the org cannot show (for example whether a Slack workspace is connected).
- A change that alters behavior for other users or callers, including overwriting values people edit by hand, unless the requirement asks for it. Field-access grants alone are not callers.

## How to ask

- Send one message, after *D1* and step 3, with intent questions only: up to 3 questions, each with options (every in-org candidate), evidence, and a recommendation.
- Record the answers as *user decisions*. An answer that adds scope becomes part of the requirement.
- Map an answer that picks no option to the option its words match, tagged *assumption*. If its words match more than one option, take the one the evidence favors.
- If the answers change the design, resend *I* (this counts as a follow-up).
- One more message is allowed in two cases:
  - a later intent fork, including a consequence of a user decision that changes behavior for other users;
  - an answer that makes a responsibility deliver nothing (for example nothing sets the chosen status).
- Unanswered values:
  - Numeric business values (thresholds, amounts, dates) become named placeholders, blocking for delivery.
  - Lists with a sensible standard set (for example picklist values) become an *assumption*.

## No question needed

- A false premise, or a data operation: produce a zero-change spec with a safe procedure.
- A partly false premise: design for the real gap.
- An undeliverable responsibility: mark it blocking for delivery, but only if the responsibility fails without it. Ask only if that defeats the main purpose.
- A component the user names that does not exist: it is a Create (*user decision*).
