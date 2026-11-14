export interface PersonalInfo {
  fullName: string;
  role: string;
  location: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
}

export interface PersonalInfoCardProps {
  data?: PersonalInfo;
  className?: string;
}

export interface InfoFieldProps {
  label: string;
  value: string;
  className?: string;
}
