// Text shown on screens. Wording follows the project rule: never claim absolute anonymity.
export const ROLE_LABELS = {
  employee: 'Employee',
  reviewer: 'Reviewer',
  ic_admin: 'IC admin',
}

export const STATUS_LABELS = {
  submitted: 'Submitted',
  under_review: 'Under review',
  escalated_to_ic: 'Escalated to IC',
  closed: 'Closed',
}

export const PRIVACY_MODES = [
  {
    value: 'identified',
    label: 'Identified',
    help: 'Your identity is attached to the complaint. Reviewers can see who filed it.',
  },
  {
    value: 'confidential',
    label: 'Confidential',
    help: 'Reviewers do not see who you are. Only the IC admin can reveal your identity, with a written reason. Role-gated and audited.',
  },
  {
    value: 'pseudonymous',
    label: 'Pseudonymous',
    help: 'Reviewers see a random alias (Reporter-xxxxxx). Only the IC admin can reveal your identity, with a written reason. Role-gated and audited.',
  },
]

export const PRIVACY_NOTE =
  'Identity is protected, not anonymous: the IC admin, and anyone with direct database access, can see who filed a complaint. Every reveal is recorded.'