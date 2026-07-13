export interface JwtPayload {
  sub: string;
  username: string;
  roles: string[];
}

export interface UserSession {
  userId: string;
  roles: string[];
}
