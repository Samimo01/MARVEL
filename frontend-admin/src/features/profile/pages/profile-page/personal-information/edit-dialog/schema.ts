import { z } from "zod";

export const personalInfoSchema = z.object({
  firstName: z.string().trim().min(1, "First name is required"),
  lastName: z.string().trim().min(1, "Last name is required"),
  email: z
    .string()
    .trim()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),
  phone: z.string().trim().min(1, "Phone number is required"),
});

export type PersonalInfoFormData = z.infer<typeof personalInfoSchema>;
