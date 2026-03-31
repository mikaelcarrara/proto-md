---
Version: 1.0.0
Model: anthropic/claude-sonnet-4
Author: platform-team
Schema:
  type: object
  properties:
    username:
      type: string
      minLength: 3
      maxLength: 20
      description: Your unique username
    email:
      type: string
      format: email
      description: Valid email address
    age:
      type: integer
      minimum: 18
      maximum: 120
      description: Your age
    notifications:
      type: boolean
      description: Receive email notifications
    role:
      type: string
      enum: [admin, user, guest]
      description: User role
    tags:
      type: array
      items:
        type: string
      minItems: 1
      maxItems: 5
      description: Your interests
  required:
    - username
    - email
---

## Context
User registration form for the platform.

## Slots
{{username}} string — username
{{email}} string — email
{{age}} int — age
{{notifications}} bool — notifications
{{role}} string — role
{{tags}} array — tags

## Constraints
1. Username must be alphanumeric.
2. Email must be valid format.
3. Age must be 18 or older.
