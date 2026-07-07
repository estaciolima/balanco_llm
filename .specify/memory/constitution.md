<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles: placeholder principle 1 -> Code Quality First; placeholder principle 2 -> Test the Behavior; placeholder principle 3 -> Consistent User Experience; placeholder principle 4 -> Performance Is a Product Requirement; placeholder principle 5 removed
- Added sections: Quality Standards; Delivery Rules
- Removed sections: template placeholder sections
- Templates requiring updates: updated `.specify/templates/plan-template.md`; updated `.specify/templates/spec-template.md`; updated `.specify/templates/tasks-template.md`
- Deferred items: none
-->

# Balanco LLM Constitution

## Core Principles

### I. Code Quality First
Code MUST be easy to read, easy to review, and aligned with the
repository's established patterns. Changes MUST stay narrowly scoped to the
problem being solved, remove dead code when touched, and avoid unnecessary
abstractions. Formatting, linting, and any repo-defined static checks MUST pass
before work is considered complete.

### II. Test the Behavior
Behavior changes MUST be covered by automated tests that prove the change and
protect against regression. New functionality MUST include tests for the happy
path and relevant edge cases, and bug fixes MUST include a regression test.
When work crosses boundaries such as API, data, UI, or service layers, the test
set MUST include the boundary that changed. Failing tests are part of the work,
not an optional follow-up.

### III. Consistent User Experience
User-facing work MUST match the product's existing interaction patterns,
content tone, spacing, states, and accessibility expectations. Loading, empty,
success, and error states are required parts of the experience. Any new surface
MUST feel native to the rest of the product instead of introducing one-off
behavior, labels, or visual treatment.

### IV. Performance Is a Product Requirement
Every feature MUST define a measurable performance expectation when runtime
cost matters to the user. Implementation MUST protect the critical path from
avoidable latency, excessive memory use, and unnecessary re-rendering or work.
Performance-sensitive changes MUST be measured before and after, and any
regression requires explicit justification and a remediation plan.

## Quality Standards

All completed work MUST satisfy the repo's formatting, linting, test, and other
automation gates relevant to the changed area. Any new dependency, pattern, or
architecture choice MUST be justified by a clear gain in quality, maintainable
scope, or user value. Changes MUST prefer the simplest design that fully meets
the requirement, and any deliberate deviation from the established code style
MUST be documented in the implementation plan.

## Delivery Rules

Specifications and plans MUST state the expected test strategy, the user-facing
consistency requirements, and the performance target or constraint that
matters for the change. Work that cannot be covered by automated tests MUST be
called out explicitly with the reason and the compensating validation method.
Known quality, UX, or performance gaps block completion until they are fixed or
explicitly accepted through the amendment process.

## Governance

This constitution overrides conflicting informal practice, branch habits, and
ad hoc guidance. Any amendment MUST be recorded in this file, propagated to the
dependent Spec Kit templates, and reviewed for impact before it becomes the new
standard.

Versioning follows semantic versioning:
- MAJOR for principle removal, redefinition, or incompatible governance change
- MINOR for a new principle or materially expanded rule set
- PATCH for clarifications, wording fixes, and non-semantic refinements

Compliance review is required in every spec, plan, and implementation review.
If a proposal violates a principle, the violation MUST appear in the relevant
complexity tracking or decision log with a specific reason and an explicit
approval trail.

**Version**: 1.0.0 | **Ratified**: 2026-06-12 | **Last Amended**: 2026-06-12
