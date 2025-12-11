<template>
  <Row :gutter="16" class="mb-4">
    <Col :span="4">
      <Card size="small" class="text-center">
        <div class="text-2xl font-bold text-blue-600">{{ safeStats.total }}</div>
        <div class="text-gray-500 text-sm">总仓库数</div>
      </Card>
    </Col>
    <Col :span="4">
      <Card size="small" class="text-center">
        <div class="text-2xl font-bold text-green-600">{{ safeStats.physical }}</div>
        <div class="text-gray-500 text-sm">实体仓</div>
      </Card>
    </Col>
    <Col :span="4">
      <Card size="small" class="text-center">
        <div class="text-2xl font-bold text-purple-600">{{ safeStats.virtual }}</div>
        <div class="text-gray-500 text-sm">虚拟仓</div>
      </Card>
    </Col>
    <Col :span="4">
      <Card size="small" class="text-center">
        <div class="text-2xl font-bold text-orange-600">{{ safeStats.domestic }}</div>
        <div class="text-gray-500 text-sm">国内仓</div>
      </Card>
    </Col>
    <Col :span="4">
      <Card size="small" class="text-center">
        <div class="text-2xl font-bold text-red-600">{{ safeStats.overseas }}</div>
        <div class="text-gray-500 text-sm">海外仓</div>
      </Card>
    </Col>
    <Col :span="4">
      <Card size="small" class="text-center">
        <div class="text-2xl font-bold text-green-600">{{ safeStats.active }}</div>
        <div class="text-gray-500 text-sm">正常运营</div>
      </Card>
    </Col>
  </Row>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Card, Row, Col } from 'ant-design-vue';

interface Stats {
  total: number;
  physical: number;
  virtual: number;
  domestic: number;
  overseas: number;
  active: number;
}

interface Props {
  stats: Stats;
}

const props = defineProps<Props>();

// 确保 stats 不为空，提供默认值
const safeStats = computed(() => {
  return props.stats || {
    total: 0,
    physical: 0,
    virtual: 0,
    domestic: 0,
    overseas: 0,
    active: 0
  };
});
</script>
