/**
 * Biometric Service - Face ID / Fingerprint authentication
 */

import * as LocalAuthentication from 'expo-local-authentication';

export type BiometricType = 'fingerprint' | 'facial' | 'iris' | 'none';

export interface BiometricStatus {
  available: boolean;
  enrolled: boolean;
  types: BiometricType[];
}

export const biometricService = {
  async isAvailable(): Promise<boolean> {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    return compatible;
  },

  async isEnrolled(): Promise<boolean> {
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    return enrolled;
  },

  async getStatus(): Promise<BiometricStatus> {
    const [available, enrolled, supportedTypes] = await Promise.all([
      LocalAuthentication.hasHardwareAsync(),
      LocalAuthentication.isEnrolledAsync(),
      LocalAuthentication.supportedAuthenticationTypesAsync(),
    ]);

    const types: BiometricType[] = supportedTypes.map((type) => {
      switch (type) {
        case LocalAuthentication.AuthenticationType.FINGERPRINT:
          return 'fingerprint';
        case LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION:
          return 'facial';
        case LocalAuthentication.AuthenticationType.IRIS:
          return 'iris';
        default:
          return 'none';
      }
    });

    return { available, enrolled, types };
  },

  async authenticate(promptMessage: string): Promise<boolean> {
    const available = await this.isAvailable();

    if (!available) {
      throw new Error('Biometric authentication is not available');
    }

    const enrolled = await this.isEnrolled();

    if (!enrolled) {
      throw new Error('No biometric credentials enrolled');
    }

    const result = await LocalAuthentication.authenticateAsync({
      promptMessage,
      cancelLabel: 'Cancel',
      disableDeviceFallback: false,
      fallbackLabel: 'Use Passcode',
    });

    return result.success;
  },

  getBiometricTypeLabel(type: BiometricType): string {
    switch (type) {
      case 'fingerprint':
        return 'Fingerprint';
      case 'facial':
        return 'Face ID';
      case 'iris':
        return 'Iris';
      default:
        return 'Biometric';
    }
  },

  async getPrimaryBiometricType(): Promise<BiometricType> {
    const status = await this.getStatus();

    if (!status.available || !status.enrolled) {
      return 'none';
    }

    if (status.types.includes('facial')) {
      return 'facial';
    }
    if (status.types.includes('fingerprint')) {
      return 'fingerprint';
    }
    if (status.types.includes('iris')) {
      return 'iris';
    }

    return 'none';
  },
};
