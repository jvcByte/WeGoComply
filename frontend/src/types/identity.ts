/**
 * Identity verification types for frontend
 * Compatible with backend unified identity response schema
 */

export interface IdentityMatchScore {
  firstname?: boolean | null;
  lastname?: boolean | null;
  dob?: boolean | null;
  phone?: boolean | null;
  email?: boolean | null;
}

export interface IdentityAddress {
  line1?: string;
  line2?: string;
  city?: string;
  lga?: string;
  state?: string;
  postal_code?: string;
}

export interface IdentityOrigin {
  state?: string;
  lga?: string;
  place?: string;
}

export interface IdentityData {
  nin?: string;
  firstname?: string;
  lastname?: string;
  middlename?: string;
  gender?: string;
  birthdate?: string;
  phone?: string;
  email?: string;
  address?: IdentityAddress;
  origin?: IdentityOrigin;
  profession?: string;
  marital_status?: string;
  educational_level?: string;
  card_status?: string;
  document_number?: string;
  photo?: string;
  signature?: string;
}

export interface IdentityResponse {
  success: boolean;
  provider: string;
  match_score?: IdentityMatchScore;
  identity?: IdentityData;
  raw?: {
    nimc_response?: any;
    [key: string]: any;
  };
  error?: string;
  message?: string;
}

export interface KYCVerifyRequest {
  verification_type: 'nin' | 'bvn' | 'face_match';
  identifier: string;
  firstname?: string;
  lastname?: string;
  dob?: string;
  phone?: string;
  email?: string;
  provider_name?: string;
}

export interface ProviderInfo {
  name: string;
  version?: string;
  supported_operations: string[];
  enabled: boolean;
  priority?: number;
  mode?: string;
  features?: string[];
}

export interface ProviderHealth {
  provider: string;
  healthy: boolean;
  last_check?: string;
  error?: string;
}

export interface NIMCTokenRequest {
  username: string;
  password: string;
  orgid: string;
}

export interface NIMCTokenResponse {
  loginMessage: {
    loginString: string;
    expireTime: string;
    loginObject: {
      username: string;
      orgid: string;
      loginTime: string;
      loginExpiryTimeInMinutes: number;
    };
  };
  loginString: string;
}

export interface NIMCSearchRequest {
  token: string;
  [key: string]: any;
}

export interface NIMCSearchResponse {
  data: any[];
  returnMessage: string;
}
