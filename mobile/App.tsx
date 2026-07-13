import React, { useEffect } from 'react';
import { SafeAreaView, StatusBar, StyleSheet, Text, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { initializeDatabase } from './src/database/sqlite';

const Stack = createNativeStackNavigator();

function LoginScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Aegis Smart Stadium OS</Text>
      <Text style={styles.subtitle}>Mobile Client Gate (Offline Enabled)</Text>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>Phase 1 Skeleton Active</Text>
      </View>
    </View>
  );
}

export default function App() {
  useEffect(() => {
    initializeDatabase().catch(err => {
      console.error('Failed to boot SQLite instance: ', err);
    });
  }, []);

  return (
    <NavigationContainer>
      <SafeAreaView style={{ flex: 1 }}>
        <StatusBar barStyle="light-content" />
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Login" component={LoginScreen} />
        </Stack.Navigator>
      </SafeAreaView>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0b10',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8
  },
  subtitle: {
    fontSize: 14,
    color: '#9ca3af',
    marginBottom: 20
  },
  badge: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.2)',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20
  },
  badgeText: {
    color: '#3b82f6',
    fontSize: 12,
    fontWeight: '600'
  }
});
