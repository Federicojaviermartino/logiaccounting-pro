/**
 * Placeholder screens for More tab
 * These provide basic structure for screens that need full implementation
 */

import React from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { Text, useTheme, Button, List, Divider } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useSelector, useDispatch } from 'react-redux';

import { spacing, colors } from '@app/theme';
import { RootState, AppDispatch } from '@store/index';
import { logout } from '@store/slices/authSlice';
import { Card, EmptyState } from '@components/common';

// Profile Screen
export const ProfileScreen: React.FC<any> = ({ navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const { user } = useSelector((state: RootState) => state.auth);

  const handleLogout = async () => {
    await dispatch(logout());
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.profileHeader}>
          <View style={[styles.avatar, { backgroundColor: theme.colors.primary }]}>
            <Text style={styles.avatarText}>
              {user?.name?.substring(0, 2).toUpperCase() || 'U'}
            </Text>
          </View>
          <Text variant="headlineSmall" style={{ color: theme.colors.onSurface }}>
            {user?.name || 'User'}
          </Text>
          <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
            {user?.email || 'user@example.com'}
          </Text>
        </View>
        <Button mode="outlined" onPress={handleLogout} style={styles.logoutButton} textColor={colors.error}>
          Sign Out
        </Button>
      </ScrollView>
    </SafeAreaView>
  );
};

// Security Settings Screen
export const SecuritySettingsScreen: React.FC<any> = () => {
  const theme = useTheme();
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Card>
          <List.Item title="Change PIN" left={(props) => <List.Icon {...props} icon="lock" />} />
          <Divider />
          <List.Item title="Biometric Settings" left={(props) => <List.Icon {...props} icon="fingerprint" />} />
          <Divider />
          <List.Item title="Auto-Lock Timer" description="5 minutes" left={(props) => <List.Icon {...props} icon="timer" />} />
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
};

// Notification Settings Screen
export const NotificationSettingsScreen: React.FC<any> = () => {
  const theme = useTheme();
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Card>
          <List.Item title="Payment Reminders" left={(props) => <List.Icon {...props} icon="bell" />} />
          <Divider />
          <List.Item title="Low Stock Alerts" left={(props) => <List.Icon {...props} icon="alert" />} />
          <Divider />
          <List.Item title="Sync Notifications" left={(props) => <List.Icon {...props} icon="sync" />} />
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
};

// Sync Settings Screen
export const SyncSettingsScreen: React.FC<any> = () => {
  const theme = useTheme();
  const { isOnline, pendingActions, lastSyncTime } = useSelector((state: RootState) => state.sync);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Card style={styles.statusCard}>
          <View style={styles.statusRow}>
            <Icon name={isOnline ? 'wifi' : 'wifi-off'} size={24} color={isOnline ? colors.success : colors.warning} />
            <Text variant="bodyLarge" style={{ color: theme.colors.onSurface }}>
              {isOnline ? 'Connected' : 'Offline'}
            </Text>
          </View>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Last sync: {lastSyncTime ? new Date(lastSyncTime).toLocaleString() : 'Never'}
          </Text>
          {pendingActions.length > 0 && (
            <Text variant="bodySmall" style={{ color: colors.warning }}>
              {pendingActions.length} pending changes
            </Text>
          )}
        </Card>
        <Button mode="contained" icon="sync" style={styles.syncButton}>
          Sync Now
        </Button>
      </ScrollView>
    </SafeAreaView>
  );
};

// Projects Screen
export const ProjectsScreen: React.FC<any> = () => {
  const theme = useTheme();
  const { projects } = useSelector((state: RootState) => state.projects);

  if (projects.length === 0) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
        <EmptyState icon="folder-outline" title="No Projects" description="Your projects will appear here" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        {projects.map((project) => (
          <Card key={project.id} style={styles.projectCard}>
            <Text variant="titleMedium" style={{ color: theme.colors.onSurface }}>{project.name}</Text>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>{project.clientName}</Text>
          </Card>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
};

// Project Detail Screen
export const ProjectDetailScreen: React.FC<any> = ({ route }) => {
  const theme = useTheme();
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <EmptyState icon="folder" title="Project Details" description="Project information coming soon" />
    </SafeAreaView>
  );
};

// Reports Screen
export const ReportsScreen: React.FC<any> = () => {
  const theme = useTheme();
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Card style={styles.reportCard}>
          <List.Item title="Financial Summary" description="Overview of income and expenses" left={(props) => <List.Icon {...props} icon="chart-pie" />} />
        </Card>
        <Card style={styles.reportCard}>
          <List.Item title="Inventory Report" description="Stock levels and movements" left={(props) => <List.Icon {...props} icon="package-variant" />} />
        </Card>
        <Card style={styles.reportCard}>
          <List.Item title="Payment Status" description="Receivables and payables" left={(props) => <List.Icon {...props} icon="cash-multiple" />} />
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
};

// Report Detail Screen
export const ReportDetailScreen: React.FC<any> = () => {
  const theme = useTheme();
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <EmptyState icon="chart-bar" title="Report Details" description="Report details coming soon" />
    </SafeAreaView>
  );
};

// Analytics Screen
export const AnalyticsScreen: React.FC<any> = () => {
  const theme = useTheme();
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <EmptyState icon="chart-line" title="Analytics" description="Business analytics coming soon" />
    </SafeAreaView>
  );
};

// Help Screen
export const HelpScreen: React.FC<any> = () => {
  const theme = useTheme();
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Card>
          <List.Item title="FAQ" left={(props) => <List.Icon {...props} icon="help-circle" />} />
          <Divider />
          <List.Item title="Contact Support" left={(props) => <List.Icon {...props} icon="email" />} />
          <Divider />
          <List.Item title="User Guide" left={(props) => <List.Icon {...props} icon="book-open" />} />
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
};

// About Screen
export const AboutScreen: React.FC<any> = () => {
  const theme = useTheme();
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.aboutHeader}>
          <View style={[styles.appIcon, { backgroundColor: theme.colors.primary }]}>
            <Text style={styles.appIconText}>LA</Text>
          </View>
          <Text variant="headlineSmall" style={{ color: theme.colors.onSurface }}>LogiAccounting Pro</Text>
          <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>Version 1.0.0</Text>
        </View>
        <Card>
          <List.Item title="Terms of Service" left={(props) => <List.Icon {...props} icon="file-document" />} />
          <Divider />
          <List.Item title="Privacy Policy" left={(props) => <List.Icon {...props} icon="shield-account" />} />
          <Divider />
          <List.Item title="Licenses" left={(props) => <List.Icon {...props} icon="license" />} />
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: spacing.md, paddingBottom: spacing.xxl },
  profileHeader: { alignItems: 'center', marginBottom: spacing.xl, paddingTop: spacing.lg },
  avatar: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md },
  avatarText: { fontSize: 28, fontWeight: '700', color: '#fff' },
  logoutButton: { marginTop: spacing.lg, borderColor: colors.error },
  statusCard: { marginBottom: spacing.md },
  statusRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.sm },
  syncButton: { marginTop: spacing.md },
  projectCard: { marginBottom: spacing.sm },
  reportCard: { marginBottom: spacing.sm },
  aboutHeader: { alignItems: 'center', marginBottom: spacing.xl, paddingTop: spacing.lg },
  appIcon: { width: 80, height: 80, borderRadius: 20, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md },
  appIconText: { fontSize: 32, fontWeight: '700', color: '#fff' },
});
