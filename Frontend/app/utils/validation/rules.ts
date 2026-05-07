import { z } from 'zod'

/**
 * Enterprise validation rules schemas for form consistency.
 */
export const validationRules = {
  email: z.string().min(1, 'Email is required').email('Invalid email address format.').trim().toLowerCase(),
  password: z.string().min(1, 'Password is required').min(6, 'Password must be at least 6 characters.')
}

export const authSchemas = {
  login: z.object({
    email: validationRules.email,
    password: validationRules.password,
    remember: z.boolean().optional()
  })
}
