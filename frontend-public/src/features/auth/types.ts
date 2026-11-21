export type AuthResponse = {
  message: string
}

export type RegistrationResponse = AuthResponse & {
  id_user: string
  nickname: string | null
  image_url: string | null
}

export type AuthSession = {
  id_user: string
  roles: RoleName[]
}

export type RoleName =
  | 'Volunteer'
  | 'Collection_Manager'
  | 'Stock_Manager'
  | 'Treasurer'
  | 'Administrator'

export type RegistrationPayload = {
  firstname: string
  lastname: string
  email: string
  password: string
  tel: string
  image?: File
}

export type LoginPayload = {
  email: string
  password: string
  rememberMe?: boolean
}
