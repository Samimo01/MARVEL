import type { FieldErrors, UseFormRegister } from "react-hook-form";

export interface PersonalInfoFormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
}

export interface PersonalDetailsFieldsProps {
  register: UseFormRegister<PersonalInfoFormData>;
  errors: FieldErrors<PersonalInfoFormData>;
}
