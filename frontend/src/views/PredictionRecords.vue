<template>
  <div class="page-wrap">
    <div class="hero-grid">
      <div class="card stat-card">
        <div class="stat-label">记录总数</div>
        <div class="stat-value">{{ records.length }}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">当前筛选</div>
        <div class="stat-value" style="font-size: 22px">{{ filteredRecords.length }}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">最新记录</div>
        <div class="stat-value" style="font-size: 18px">{{ latestRecordText }}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">当前钻井</div>
        <div class="stat-value" style="font-size: 18px">{{ selectedWellLabel }}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-hd">
        <div>
          <div class="panel-title">预测记录</div>
          <div class="panel-subtitle">查看全部历史预测，支持按钻井筛选和详情跳转</div>
        </div>
        <div class="toolbar-right">
          <el-select v-model="selectedWellId" class="search-box" placeholder="全部钻井" clearable filterable @change="reload">
            <el-option v-for="well in wells" :key="well.id" :label="well.name" :value="well.id" />
          </el-select>
          <el-input v-model="keyword" class="search-box" placeholder="搜索模型名 / 钻井名" clearable />
          <el-button @click="reload">刷新</el-button>
        </div>
      </div>

      <div class="panel-body">
        <el-table v-loading="loading" :data="filteredRecords" height="620" @row-click="openDetail">
          <el-table-column prop="id" label="记录ID" width="100" />
          <el-table-column prop="well_name" label="钻井" min-width="160" />
          <el-table-column prop="model_name" label="模型" min-width="180" />
          <el-table-column label="时间" min-width="180">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="R" width="100">
            <template #default="{ row }">{{ metric(row, 'R') }}</template>
          </el-table-column>
          <el-table-column label="R2" width="100">
            <template #default="{ row }">{{ metric(row, 'R2') }}</template>
          </el-table-column>
          <el-table-column label="MAE" width="100">
            <template #default="{ row }">{{ metric(row, 'MAE') }}</template>
          </el-table-column>
          <el-table-column label="RMSE" width="100">
            <template #default="{ row }">{{ metric(row, 'RMSE') }}</template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click.stop="openDetail(row)">查看详情</el-button>
              <el-button link type="success" @click.stop="goPredict(row)">打开预测页</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-drawer v-model="drawerVisible" title="预测详情" size="520px">
      <el-skeleton v-if="detailLoading" :rows="6" animated />
      <template v-else-if="detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="记录ID">{{ detail.id }}</el-descriptions-item>
          <el-descriptions-item label="钻井">{{ detail.well_name }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ detail.model_name }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(detail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="R">{{ metric(detail, 'R') }}</el-descriptions-item>
          <el-descriptions-item label="R2">{{ metric(detail, 'R2') }}</el-descriptions-item>
          <el-descriptions-item label="MAE">{{ metric(detail, 'MAE') }}</el-descriptions-item>
          <el-descriptions-item label="RMSE">{{ metric(detail, 'RMSE') }}</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 16px; display: flex; justify-content: flex-end; gap: 12px">
          <el-button @click="drawerVisible = false">关闭</el-button>
          <el-button type="primary" @click="goPredict(detail)">打开预测页</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const router = useRouter()

const loading = ref(false)
const detailLoading = ref(false)
const wells = ref([])
const records = ref([])
const keyword = ref('')
const selectedWellId = ref('')
const drawerVisible = ref(false)
const detail = ref(null)

const filteredRecords = computed(() => {
  const term = keyword.value.trim().toLowerCase()
  return records.value.filter((item) => {
    const wellMatch = !selectedWellId.value || String(item.well_id) === String(selectedWellId.value)
    const textMatch =
      !term ||
      [item.well_name, item.model_name].some((value) => String(value || '').toLowerCase().includes(term))
    return wellMatch && textMatch
  })
})

const latestRecordText = computed(() => {
  const row = records.value[0]
  return row ? `#${row.id}` : '-'
})

const selectedWellLabel = computed(() => {
  if (!selectedWellId.value) return '全部'
  return wells.value.find((item) => String(item.id) === String(selectedWellId.value))?.name || '-'
})

function formatTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function metric(row, key) {
  const value = row?.metrics?.[key]
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '-'
  return Number(value).toFixed(4)
}

async function reload() {
  loading.value = true
  try {
    const [wellData, recordData] = await Promise.all([api.wells(), api.listPredictions()])
    wells.value = wellData
    records.value = recordData
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function openDetail(row) {
  drawerVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = await api.prediction(row.id)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    detailLoading.value = false
  }
}

function goPredict(row) {
  router.push({ name: 'predict', query: { predictionId: row.id } })
}

onMounted(reload)
</script>
