import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { SafeAreaView, Text, TouchableOpacity, StyleSheet } from "react-native";
import CategoryScreen from "./screens/CategoryScreen";
import TopicDetail from "./screens/TopicDetail";

const Stack = createNativeStackNavigator();

// Demo data – později můžeš nahradit fetch/JSONem
const DEMO_TOPICS = [
  { id: "t1", title: "Lineární algebra", description: "Matice, vektory, SVD", progress: 0, tasks: ["Matice", "Soustavy", "SVD"] },
  { id: "t2", title: "Pravděpodobnost", description: "Distribuce, CLT", progress: 0, tasks: ["Distribuce", "Bayes", "CLT"] },
];

function Home({ navigation }) {
  return (
    <SafeAreaView style={{ flex: 1, padding: 16 }}>
      <Text style={{ fontSize: 22, fontWeight: "800", marginBottom: 12 }}>Kategorie</Text>
      <TouchableOpacity
        style={styles.tile}
        onPress={() => navigation.navigate("Category", { categoryName: "Matematické základy", topics: DEMO_TOPICS })}
      >
        <Text style={styles.tileTitle}>Matematické základy</Text>
        <Text style={styles.tileSub}>2 lekce</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Home" component={Home} options={{ title: "Domů" }} />
        <Stack.Screen name="Category" component={CategoryScreen} options={{ headerShown: false }} />
        <Stack.Screen name="TopicDetail" component={TopicDetail} options={{ headerShown: false }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  tile: { backgroundColor: "#fff", padding: 16, borderRadius: 14, marginBottom: 12, elevation: 2 },
  tileTitle: { fontSize: 18, fontWeight: "700" },
  tileSub: { color: "#666", marginTop: 4 },
});
