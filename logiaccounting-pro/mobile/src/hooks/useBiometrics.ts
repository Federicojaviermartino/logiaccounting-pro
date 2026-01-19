/**
 * useBiometrics Hook
 * Biometric authentication utilities
 */

import { useState, useEffect, useCallback } from 'react';
import { biometricService, BiometricStatus } from '@services/index';

export const useBiometrics = () => {
  const [status, setStatus] = useState<BiometricStatus>({
    available: false,
    biometryType: null,
    enrolled: false,
  });
  const [biometryName, setBiometryName] = useState<string>('Biometric');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkBiometrics();
  }, []);

  const checkBiometrics = useCallback(async () => {
    setIsLoading(true);
    try {
      const biometricStatus = await biometricService.checkAvailability();
      setStatus(biometricStatus);

      if (biometricStatus.available) {
        const name = await biometricService.getBiometryTypeName();
        setBiometryName(name);
      }
    } catch (error) {
      console.error('Error checking biometrics:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const authenticate = useCallback(async (message?: string) => {
    if (!status.available) {
      return false;
    }
    return biometricService.authenticate(message);
  }, [status.available]);

  const enable = useCallback(async () => {
    if (!status.available) {
      return false;
    }
    const success = await biometricService.enable();
    await checkBiometrics();
    return success;
  }, [status.available, checkBiometrics]);

  const disable = useCallback(async () => {
    const success = await biometricService.disable();
    await checkBiometrics();
    return success;
  }, [checkBiometrics]);

  return {
    // Status
    isAvailable: status.available,
    biometryType: status.biometryType,
    biometryName,
    isEnrolled: status.enrolled,
    isLoading,

    // Actions
    authenticate,
    enable,
    disable,
    refresh: checkBiometrics,
  };
};

export default useBiometrics;
