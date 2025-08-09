import React, { useEffect, useMemo, useState } from "react";
import { View, Text, StyleSheet, SafeAreaView, ScrollView, Alert } from "react-native";
import { TouchableOpacity } from "react-native-gesture-handler";
import TaskItem from "../components/TaskItem";
import { getTopicProgress, setTaskDone, markTopicCompleted } from "../utils/progress";
import { LinearGradient } from "expo-linear-gradient";

export default function TopicDetail({ route, navigation }) {
  const { topic } = route.params;
  // očekáváme tvar: { id, title, description, tasks: string[] }
  const [doneSet, setDoneSet] = useState(new Set());
  const [loading, setLoading] = useState(true);

  const total = topic?.tasks?.length || 0;
  const doneCount = doneSet.size;
  const percent = total > 0 ? Math.round((doneCount / total) * 100) : 0;
  const isAllDone = total > 0 && doneCount === total;

  useEffect(() => {
    let mounted = true;
    (async () => {
      const saved = await getTopicProgress(topic.id);
      if (mounted) {
        setDoneSet(new Set(saved));
        setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [topic?.id]);

  useEffect(() => {
    navigation.setOptions?.({ title: topic.title || "Detail lekce" });
  }, [navigation, topic?.title]);

  const onToggleTask = async (index, value) => {
    const next = new Set(doneSet);
    if (value) next.add(index);
    else next.delete(index);
    setDoneSet(next);
    await setTaskDone(topic.id, index, value);

    // auto-complete celé téma, pokud je všechno hotovo
    if (topic.tasks && next.size === topic.tasks.length) {
      await markTopicCompleted(topic.id);
      Alert.alert("🎉 Hotovo!", "Lekce dokončena. Skvělá práce!");
    }
  };

  const onCompletePress = async () => {
    if (!isAllDone) {
      Alert.alert("Ještě ne úplně", "Nejprve dokonči všechny úkoly v seznamu.");
      return;
    }
    await markTopicCompleted(topic.id);
    Alert.alert("🎉 Hotovo!", "Lekce dokončena. Skvělá práce!");
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={{ paddingBottom: 32 }} showsVerticalScrollIndicator={false}>
        <LinearGradient colors={["#4facfe", "#00f2fe"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
          <Text style={styles.heroTitle}>{topic.title}</Text>
          <Text style={styles.heroDesc}>{topic.description}</Text>

          <View style={styles.progressRow}>
            <View style={styles.progressBarBg}>
              <View style={[styles.progressFill, { width: `${percent}%` }]} />
            </View>
            <Text style={styles.progressPct}>{percent}%</Text>
          </View>
        </LinearGradient>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Úkoly</Text>
          {loading ? (
            <Text style={{ color: "#666" }}>Načítám…</Text>
          ) : topic?.tasks?.length ? (
            topic.tasks.map((t, i) => (
              <TaskItem key={i} label={t} value={doneSet.has(i)} onChange={(v) => onToggleTask(i, v)} />
            ))
          ) : (
            <Text style={{ color: "#666" }}>Tato lekce zatím nemá definované úkoly.</Text>
          )}
        </View>

        <TouchableOpacity
          activeOpacity={0.85}
          onPress={onCompletePress}
          style={[styles.completeBtn, !isAllDone && { opacity: 0.5 }]}
        >
          <Text style={styles.completeBtnText}>✔ Označit lekci jako hotovou</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f7fa" },
  hero: {
    paddingVertical: 18,
    paddingHorizontal: 16,
    borderBottomLeftRadius: 18,
    borderBottomRightRadius: 18,
    marginBottom: 14,
  },
  heroTitle: { color: "#fff", fontSize: 22, fontWeight: "800", marginBottom: 6 },
  heroDesc: { color: "#eaf6ff", fontSize: 14 },
  progressRow: { marginTop: 14, flexDirection: "row", alignItems: "center", gap: 10 },
  progressBarBg: { flex: 1, height: 10, borderRadius: 999, backgroundColor: "rgba(255,255,255,0.35)" },
  progressFill: { height: "100%", borderRadius: 999, backgroundColor: "#fff" },
  progressPct: { color: "#fff", fontWeight: "700" },

  section: { paddingHorizontal: 16, marginTop: 8 },
  sectionTitle: { fontSize: 18, fontWeight: "700", color: "#333", marginBottom: 8 },

  completeBtn: {
    marginTop: 16,
    marginHorizontal: 16,
    backgroundColor: "#22c55e",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  completeBtnText: { color: "white", fontWeight: "800", fontSize: 16 },
});
