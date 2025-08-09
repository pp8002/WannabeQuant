import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, SafeAreaView } from 'react-native';
import TopicCard from '../components/TopicCard';
import { getTopicProgress } from '../utils';

const CategoryScreen = ({ route, navigation }) => {
  const { categoryName, topics } = route.params;
  const [items, setItems] = useState(topics || []);

  useEffect(() => {
    // načti skutečný progress z AsyncStorage a dopočti %
    (async () => {
      const enriched = [];
      for (const t of topics || []) {
        const done = new Set(await getTopicProgress(t.id));
        const total = Array.isArray(t.tasks) ? t.tasks.length : 0;
        const pct = total > 0 ? Math.round((done.size / total) * 100) : (t.progress || 0);
        enriched.push({ ...t, progress: pct });
      }
      setItems(enriched);
    })();
  }, [topics]);

  const handleTopicPress = (topic) => {
    navigation.navigate('TopicDetail', { topic });
  };

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.header}>{categoryName}</Text>
      <FlatList
        data={items}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <TopicCard
            title={item.title}
            description={item.description}
            progress={item.progress ?? 0}
            icon={item.icon}
            onPress={() => handleTopicPress(item)}
          />
        )}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 40 }}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa', paddingHorizontal: 16, paddingTop: 10 },
  header: { fontSize: 26, fontWeight: '700', color: '#333', marginBottom: 20 },
});

export default CategoryScreen;
