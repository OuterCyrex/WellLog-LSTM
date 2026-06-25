<template>
  <div class="page-wrap prediction-page">
    <div class="metrics-grid prediction-history">
      <div class="card stat-card summary-card">
        <div class="stat-label">R</div>
        <div class="stat-value">{{ metricText('R') || '-' }}</div>
      </div>
      <div class="card stat-card summary-card">
        <div class="stat-label">R2</div>
        <div class="stat-value">{{ metricText('R2') || '-' }}</div>
      </div>
      <div class="card stat-card summary-card">
        <div class="stat-label">MAE</div>
        <div class="stat-value">{{ metricText('MAE') || '-' }}</div>
      </div>
      <div class="card stat-card summary-card">
        <div class="stat-label">RMSE</div>
        <div class="stat-value">{{ metricText('RMSE') || '-' }}</div>
      </div>
    </div>

    <div class="panel-body prediction-stage">
      <div v-if="loading" class="empty-state prediction-empty">正在加载预测数据...</div>
      <div v-else-if="!currentPrediction" class="empty-state prediction-empty">请选择一口钻井并加载预测记录</div>
      <template v-else>
        <div class="panel chart-card">
          <div class="panel-hd">
            <div>
              <div class="panel-title">钻井预测</div>
              <div class="panel-subtitle">{{ currentWellName }} · 记录 #{{ currentPredictionId }}</div>
            </div>
            <div class="toolbar-right">
              <el-tag>{{ pointCount }} 个样本点</el-tag>
              <el-select v-model="selectedWellId" class="search-box" placeholder="选择钻井" filterable @change="handleWellChange">
                <el-option v-for="well in wells" :key="well.id" :label="well.name" :value="String(well.id)" />
              </el-select>
              <el-select v-model="selectedPredictionId" class="search-box" placeholder="选择预测记录" filterable @change="handlePredictionChange">
                <el-option v-for="item in predictions" :key="item.id" :label="`#${item.id} · ${formatTime(item.created_at)}`" :value="String(item.id)" />
              </el-select>
              <el-button @click="reload">刷新</el-button>
            </div>
          </div>
          <div class="panel-body">
            <div ref="mainChartRef" class="chart-box"></div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const wells = ref([])
const predictions = ref([])
const currentPrediction = ref(null)
const selectedWellId = ref('')
const selectedPredictionId = ref('')
const mainChartRef = ref()

let mainChart

const currentWellName = computed(() => wells.value.find((item) => item.id === Number(selectedWellId.value))?.name || '')
const currentPredictionId = computed(() => currentPrediction.value?.id || '')
const pointCount = computed(() => currentPrediction.value?.depth?.length || 0)

function formatTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function metricText(key) {
  const value = currentPrediction.value?.metrics?.[key]
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '-'
  return Number(value).toFixed(4)
}

function normalizePrediction(detail) {
  const depth = Array.isArray(detail?.depth) ? detail.depth.map(Number) : []
  const yTrue = Array.isArray(detail?.y_true) ? detail.y_true.map(Number) : []
  const yPred = Array.isArray(detail?.y_pred) ? detail.y_pred.map(Number) : []
  return depth.map((item, index) => ({
    depth: Number(item),
    yTrue: Number(yTrue[index]),
    yPred: Number(yPred[index]),
    residual: Number(yPred[index]) - Number(yTrue[index]),
  }))
}

function disposeCharts() {
  mainChart?.dispose()
  mainChart = null
}

function resizeCharts() {
  mainChart?.resize()
}

function renderChart() {
  if (!currentPrediction.value || !mainChartRef.value) return
  const rows = normalizePrediction(currentPrediction.value)
  nextTick(() => {
    mainChart = mainChart || echarts.init(mainChartRef.value)
    mainChart.setOption({
      backgroundColor: 'transparent',
      animationDuration: 500,
      tooltip: { trigger: 'axis', axisPointer: { type: 'line' } },
      legend: { top: 8, textStyle: { color: '#334155' } },
      grid: { left: 24, right: 18, top: 48, bottom: 36, containLabel: true },
      xAxis: {
        type: 'value',
        name: 'Depth',
        min: 'dataMin',
        max: 'dataMax',
        boundaryGap: false,
        scale: true,
        axisLabel: { color: '#64748b' },
        axisLine: { lineStyle: { color: 'rgba(31,41,55,0.25)' } },
        splitLine: { lineStyle: { color: 'rgba(31,41,55,0.08)' } },
      },
      yAxis: {
        type: 'value',
        name: 'Value',
        scale: true,
        axisLabel: { color: '#64748b' },
        axisLine: { lineStyle: { color: 'rgba(31,41,55,0.25)' } },
        splitLine: { lineStyle: { color: 'rgba(31,41,55,0.08)' } },
      },
      series: [
        { name: '实测', type: 'line', smooth: false, showSymbol: false, data: rows.map((row) => [row.depth, row.yTrue]), lineStyle: { width: 2, color: '#06b6d4' } },
        { name: '预测', type: 'line', smooth: false, showSymbol: false, data: rows.map((row) => [row.depth, row.yPred]), lineStyle: { width: 2, color: '#2563eb' } },
      ],
    })
  })
}

async function loadWells() {
  wells.value = await api.wells()
  const routeWellId = route.query.wellId ? String(route.query.wellId) : '';
  const hasRouteWell = routeWellId && wells.value.some((item) => String(item.id) === routeWellId)
  if (hasRouteWell && !selectedWellId.value) {
    selectedWellId.value = routeWellId
  } else if (!selectedWellId.value && wells.value.length > 0) {
    selectedWellId.value = String(wells.value[0].id)
  }
}

async function loadPredictions(wellId, preferredPredictionId = null, detailOverride = null) {
  if (!wellId) {
    predictions.value = []
    currentPrediction.value = null
    selectedPredictionId.value = ''
    return
  }

  predictions.value = await api.listPredictions(wellId)
  const routePredictionId = preferredPredictionId ? Number(preferredPredictionId) : null
  const preferId = routePredictionId && predictions.value.some((item) => item.id === routePredictionId)
    ? routePredictionId
    : predictions.value[0]?.id

  selectedPredictionId.value = preferId ? String(preferId) : ''
  if (preferId) {
    if (detailOverride && Number(detailOverride.id) === Number(preferId)) {
      currentPrediction.value = detailOverride
      renderChart()
    } else {
      await loadPredictionDetail(preferId)
    }
  } else {
    currentPrediction.value = null
  }
}

async function loadPredictionDetail(predictionId) {
  if (!predictionId) {
    currentPrediction.value = null
    return
  }
  currentPrediction.value = await api.prediction(predictionId)
  renderChart()
}

async function handleWellChange() {
  router.replace({ name: 'predict', query: { wellId: selectedWellId.value } })
  await loadPredictions(selectedWellId.value)
}

async function handlePredictionChange() {
  if (!selectedPredictionId.value) return
  router.replace({ name: 'predict', query: { wellId: selectedWellId.value, predictionId: selectedPredictionId.value } })
  await loadPredictionDetail(selectedPredictionId.value)
}

async function reload() {
  loading.value = true
  try {
    const routePredictionId = route.query.predictionId ? String(route.query.predictionId) : ''
    const routeWellId = route.query.wellId ? String(route.query.wellId) : ''
    let routeDetail = null

    if (routePredictionId) {
      routeDetail = await api.prediction(routePredictionId)
      selectedPredictionId.value = routePredictionId
      if (routeDetail?.well_id) {
        selectedWellId.value = String(routeDetail.well_id)
      }
    } else if (routeWellId) {
      selectedWellId.value = routeWellId
    }

    await loadWells()
    if (!selectedWellId.value && routeWellId) {
      selectedWellId.value = routeWellId
    }
    await loadPredictions(selectedWellId.value, routePredictionId || null, routeDetail)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

watch(
  () => route.query,
  async (query) => {
    const wellId = query.wellId ? String(query.wellId) : ''
    const predictionId = query.predictionId ? String(query.predictionId) : ''

    if (predictionId && predictionId !== String(selectedPredictionId.value)) {
      await reload()
      return
    }

    if (wellId && wellId !== String(selectedWellId.value)) {
      selectedWellId.value = wellId
      await loadPredictions(selectedWellId.value)
    }
  },
  { deep: true },
)

onMounted(async () => {
  await reload()
  window.addEventListener('resize', resizeCharts)
})

watch(
  () => [loading.value, currentPrediction.value?.id, mainChartRef.value],
  async ([isLoading, predictionId, chartEl]) => {
    if (isLoading || !predictionId || !chartEl) return
    await nextTick()
    renderChart()
  },
  { flush: 'post' },
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})
</script>
