/**
 * Biometric Authentication Service
 * Handles Face ID, Touch ID, and Fingerprint authentication
 */

import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';
import * as Keychain from 'react-native-keychain';

const rnBiometrics = new ReactNativeBiometrics();

export interface BiometricStatus {
  available: boolean;
  biometryType: BiometryTypes | null;
  enrolled: boolean;
}

const BIOMETRIC_KEY_SERVICE = 'com.logiaccounting.biometric';

export const biometricService = {
  /**
   * Check if biometrics are available
   */
  checkAvailability: async (): Promise<BiometricStatus> => {
    try {
      const { available, biometryType } = await rnBiometrics.isSensorAvailable();
      return {
        available,
        biometryType: biometryType || null,
        enrolled: available,
      };
    } catch (error) {
      return {
        available: false,
        biometryType: null,
        enrolled: false,
      };
    }
  },

  /**
   * Get biometry type name
   */
  getBiometryTypeName: async (): Promise<string> => {
    const { biometryType } = await rnBiometrics.isSensorAvailable();

    switch (biometryType) {
      case BiometryTypes.FaceID:
        return 'Face ID';
      case BiometryTypes.TouchID:
        return 'Touch ID';
      case BiometryTypes.Biometrics:
        return 'Fingerprint';
      default:
        return 'Biometric';
    }
  },

  /**
   * Authenticate with biometrics
   */
  authenticate: async (promptMessage?: string): Promise<boolean> => {
    try {
      const { success } = await rnBiometrics.simplePrompt({
        promptMessage: promptMessage || 'Authenticate to continue',
        cancelButtonText: 'Cancel',
      });
      return success;
    } catch (error) {
      console.error('Biometric authentication error:', error);
      return false;
    }
  },

  /**
   * Create biometric keys for secure authentication
   */
  createKeys: async (): Promise<boolean> => {
    try {
      const { publicKey } = await rnBiometrics.createKeys();

      // Store public key for verification
      await Keychain.setGenericPassword('biometricKey', publicKey, {
        service: BIOMETRIC_KEY_SERVICE,
      });

      return true;
    } catch (error) {
      console.error('Error creating biometric keys:', error);
      return false;
    }
  },

  /**
   * Delete biometric keys
   */
  deleteKeys: async (): Promise<boolean> => {
    try {
      await rnBiometrics.deleteKeys();
      await Keychain.resetGenericPassword({ service: BIOMETRIC_KEY_SERVICE });
      return true;
    } catch (error) {
      console.error('Error deleting biometric keys:', error);
      return false;
    }
  },

  /**
   * Check if biometric keys exist
   */
  keysExist: async (): Promise<boolean> => {
    try {
      const { keysExist } = await rnBiometrics.biometricKeysExist();
      return keysExist;
    } catch (error) {
      return false;
    }
  },

  /**
   * Create signature with biometrics
   */
  createSignature: async (payload: string): Promise<string | null> => {
    try {
      const { success, signature } = await rnBiometrics.createSignature({
        promptMessage: 'Authenticate to sign',
        payload,
      });

      return success ? signature : null;
    } catch (error) {
      console.error('Error creating signature:', error);
      return null;
    }
  },

  /**
   * Enable biometric authentication
   */
  enable: async (): Promise<boolean> => {
    const { available } = await biometricService.checkAvailability();

    if (!available) {
      return false;
    }

    // Create keys if they don't exist
    const keysExist = await biometricService.keysExist();
    if (!keysExist) {
      return await biometricService.createKeys();
    }

    return true;
  },

  /**
   * Disable biometric authentication
   */
  disable: async (): Promise<boolean> => {
    return await biometricService.deleteKeys();
  },
};

export default biometricService;
