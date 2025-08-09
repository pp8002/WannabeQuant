import React from "react";
import { View, Text, StyleSheet } from "react-native";
import Checkbox from "expo-checkbox";

export default function TaskItem({ label, value, onChange }) {
  return (
    <View style={styles.row}>
      <Checkbox value={value} onValueChange={onChange} color={value ? "#22c55e" : undefined} />
      <Text style={[styles.text, value && styles.done]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: "#fff",
    borderRadius: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 8,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  text: { color: "#333", fontSize: 14, flex: 1 },
  done: { color: "#999", textDecorationLine: "line-through" },
});
