import { z } from 'zod'

/**
 * Enterprise validation rules schemas for form consistency.
 */
export const validationRules = {
  email: z.string().min(1, 'Email is required').email('Invalid email address format.').trim().toLowerCase(),
  password: z.string().min(1, 'Password is required').min(6, 'Password must be at least 6 characters.')
}

const setupPassword = z
  .string()
  .min(1, 'Password is required')
  .min(8, 'Password must be at least 8 characters.')

export const authSchemas = {
  login: z.object({
    email: validationRules.email,
    password: validationRules.password,
    remember: z.boolean().optional()
  }),
  setup: z
    .object({
      name: z.string().min(1, 'Name is required').max(120, 'Name is too long').trim(),
      email: validationRules.email,
      password: setupPassword,
      passwordConfirm: z.string().min(1, 'Please confirm your password')
    })
    .refine((data) => data.password === data.passwordConfirm, {
      message: 'Passwords do not match',
      path: ['passwordConfirm']
    })
}
