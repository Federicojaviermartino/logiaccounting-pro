/**
 * Storage Service
 * Secure storage for app data
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Keychain from 'react-native-keychain';

const STORAGE_PREFIX = '@logiaccounting:';

export const storageService = {
  /**
   * Get item from AsyncStorage
   */
  getItem: async <T>(key: string): Promise<T | null> => {
    try {
      const value = await AsyncStorage.getItem(`${STORAGE_PREFIX}${key}`);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      console.error(`Error getting item ${key}:`, error);
      return null;
    }
  },

  /**
   * Set item in AsyncStorage
   */
  setItem: async <T>(key: string, value: T): Promise<boolean> => {
    try {
      await AsyncStorage.setItem(
        `${STORAGE_PREFIX}${key}`,
        JSON.stringify(value)
      );
      return true;
    } catch (error) {
      console.error(`Error setting item ${key}:`, error);
      return false;
    }
  },

  /**
   * Remove item from AsyncStorage
   */
  removeItem: async (key: string): Promise<boolean> => {
    try {
      await AsyncStorage.removeItem(`${STORAGE_PREFIX}${key}`);
      return true;
    } catch (error) {
      console.error(`Error removing item ${key}:`, error);
      return false;
    }
  },

  /**
   * Get multiple items
   */
  multiGet: async <T>(keys: string[]): Promise<Record<string, T | null>> => {
    try {
      const prefixedKeys = keys.map((k) => `${STORAGE_PREFIX}${k}`);
      const pairs = await AsyncStorage.multiGet(prefixedKeys);

      return pairs.reduce((acc, [key, value]) => {
        const cleanKey = key.replace(STORAGE_PREFIX, '');
        acc[cleanKey] = value ? JSON.parse(value) : null;
        return acc;
      }, {} as Record<string, T | null>);
    } catch (error) {
      console.error('Error getting multiple items:', error);
      return {};
    }
  },

  /**
   * Set multiple items
   */
  multiSet: async <T>(items: Record<string, T>): Promise<boolean> => {
    try {
      const pairs: [string, string][] = Object.entries(items).map(
        ([key, value]) => [`${STORAGE_PREFIX}${key}`, JSON.stringify(value)]
      );
      await AsyncStorage.multiSet(pairs);
      return true;
    } catch (error) {
      console.error('Error setting multiple items:', error);
      return false;
    }
  },

  /**
   * Clear all app storage
   */
  clear: async (): Promise<boolean> => {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const appKeys = keys.filter((k) => k.startsWith(STORAGE_PREFIX));
      await AsyncStorage.multiRemove(appKeys);
      return true;
    } catch (error) {
      console.error('Error clearing storage:', error);
      return false;
    }
  },

  /**
   * Get all storage keys
   */
  getAllKeys: async (): Promise<string[]> => {
    try {
      const keys = await AsyncStorage.getAllKeys();
      return keys
        .filter((k) => k.startsWith(STORAGE_PREFIX))
        .map((k) => k.replace(STORAGE_PREFIX, ''));
    } catch (error) {
      console.error('Error getting all keys:', error);
      return [];
    }
  },

  // Secure storage using Keychain

  /**
   * Store sensitive data securely
   */
  setSecure: async (
    key: string,
    value: string,
    options?: Keychain.Options
  ): Promise<boolean> => {
    try {
      await Keychain.setGenericPassword(key, value, {
        service: `com.logiaccounting.${key}`,
        ...options,
      });
      return true;
    } catch (error) {
      console.error(`Error setting secure item ${key}:`, error);
      return false;
    }
  },

  /**
   * Get sensitive data
   */
  getSecure: async (key: string): Promise<string | null> => {
    try {
      const credentials = await Keychain.getGenericPassword({
        service: `com.logiaccounting.${key}`,
      });
      return credentials ? credentials.password : null;
    } catch (error) {
      console.error(`Error getting secure item ${key}:`, error);
      return null;
    }
  },

  /**
   * Remove sensitive data
   */
  removeSecure: async (key: string): Promise<boolean> => {
    try {
      await Keychain.resetGenericPassword({
        service: `com.logiaccounting.${key}`,
      });
      return true;
    } catch (error) {
      console.error(`Error removing secure item ${key}:`, error);
      return false;
    }
  },
};

export default storageService;
