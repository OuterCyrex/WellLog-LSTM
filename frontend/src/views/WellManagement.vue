<template>
  <div class="page-wrap">
    <div class="hero-grid">
      <div v-for="card in statCards" :key="card.label" class="card stat-card">
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value">{{ card.value }}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-hd">
        <div>
          <div class="panel-title">钻井管理</div>
          <div class="panel-subtitle">创建井、导入文件、发起预测</div>
        </div>
        <div class="toolbar-right">
          <el-button type="primary" @click="openCreate">新增钻井</el-button>
          <el-button @click="reload">刷新</el-button>
        </div>
      </div>

      <div class="panel-body">
        <div class="toolbar">
          <div class="toolbar-left">
            <el-input v-model="keyword" class="search-box" placeholder="搜索名称 / 位置 / 备注" clearable />
          </div>
          <div class="toolbar-right">
            <el-tag effect="dark" type="info">共 {{ filteredWells.length }} 口井</el-tag>
          </div>
        </div>

        <div class="table-card" style="margin-top: 16px">
          <el-table :data="filteredWells" v-loading="loading" height="540">
            <el-table-column prop="name" label="钻井名称" min-width="160" />
            <el-table-column prop="location" label="位置" min-width="140" />
            <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
            <el-table-column prop="import_count" label="导入数" width="90" align="center" />
            <el-table-column prop="prediction_count" label="预测数" width="90" align="center" />
            <el-table-column label="操作" width="300" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
                <el-button link type="primary" @click="openImports(row)">导入记录</el-button>
                <el-button link type="success" @click="triggerUpload(row)">上传 CSV</el-button>
                <el-button link type="warning" @click="runPrediction(row.id)">预测</el-button>
                <el-button link type="danger" @click="removeWell(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
        <div class="form-grid">
          <el-form-item label="钻井名称" prop="name">
            <el-input v-model="form.name" placeholder="例如：Well-01" />
          </el-form-item>
          <el-form-item label="位置" prop="location">
            <el-input v-model="form.location" placeholder="例如：A 区块" />
          </el-form-item>
        </div>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="4" placeholder="补充说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <el-drawer v-model="importDrawerVisible" :title="importDrawerTitle" size="480px">
      <div class="panel-subtitle" style="margin-bottom: 12px">上传后会存到后端内存库，预测会直接读取最新导入。</div>
      <el-skeleton v-if="importLoading" :rows="6" animated />
      <div v-else class="import-list">
        <div v-if="imports.length === 0" class="empty-state">暂无导入记录</div>
        <div v-for="item in imports" :key="item.id" class="import-item">
          <div>
            <div class="import-item-title">{{ item.original_name }}</div>
            <div class="import-item-meta">大小：{{ item.row_count }} 字节</div>
          </div>
          <div>
            <el-button size="small" type="primary" @click="runPrediction(currentImportWellId, item.id)">用此批次预测</el-button>
          </div>
        </div>
      </div>
    </el-drawer>

    <input ref="fileInputRef" class="hidden-file" type="file" accept=".csv" @change="handleFileChange" />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { getSession } from '../auth'

const router = useRouter()
const currentUser = getSession()

const loading = ref(false)
const saving = ref(false)
const keyword = ref('')
const wells = ref([])
const summary = ref({ wells: 0, imports: 0, predictions: 0, latest_prediction: null })
const dialogVisible = ref(false)
const dialogTitle = ref('新增钻井')
const formRef = ref()
const form = reactive({ id: null, name: '', location: '', remark: '' })
const importDrawerVisible = ref(false)
const importDrawerTitle = ref('导入记录')
const currentImportWellId = ref(null)
const imports = ref([])
const importLoading = ref(false)
const fileInputRef = ref()
const uploadWellId = ref(null)

const rules = {
  name: [{ required: true, message: '请输入钻井名称', trigger: 'blur' }],
}

const filteredWells = computed(() => {
  const term = keyword.value.trim().toLowerCase()
  if (!term) return wells.value
  return wells.value.filter((item) =>
    [item.name, item.location, item.remark].some((field) => String(field || '').toLowerCase().includes(term)),
  )
})

const statCards = computed(() => [
  { label: '钻井总数', value: summary.value.wells ?? 0 },
  { label: 'CSV 导入', value: summary.value.imports ?? 0 },
  { label: '预测次数', value: summary.value.predictions ?? 0 },
  { label: '当前用户', value: currentUser?.username || '-' },
])

function resetForm() {
  form.id = null
  form.name = ''
  form.location = ''
  form.remark = ''
}

function openCreate() {
  resetForm()
  dialogTitle.value = '新增钻井'
  dialogVisible.value = true
}

function openEdit(row) {
  form.id = row.id
  form.name = row.name
  form.location = row.location || ''
  form.remark = row.remark || ''
  dialogTitle.value = '编辑钻井'
  dialogVisible.value = true
}

async function reload() {
  loading.value = true
  try {
    const [summaryData, wellData] = await Promise.all([api.summary(), api.wells()])
    summary.value = summaryData
    wells.value = wellData
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const payload = {
        name: form.name.trim(),
        location: form.location.trim() || null,
        remark: form.remark.trim() || null,
        ownerUserId: currentUser?.id,
      }
      if (form.id) {
        await api.updateWell(form.id, payload)
      } else {
        await api.createWell(payload)
      }
      dialogVisible.value = false
      await reload()
    } catch (error) {
      ElMessage.error(error.message)
    } finally {
      saving.value = false
    }
  })
}

async function removeWell(row) {
  try {
    await ElMessageBox.confirm(`确认删除钻井「${row.name}」吗？`, '提示', { type: 'warning' })
    await api.deleteWell(row.id)
    ElMessage.success('已删除')
    await reload()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.message)
  }
}

async function openImports(row) {
  currentImportWellId.value = row.id
  importDrawerTitle.value = `${row.name} 导入记录`
  importDrawerVisible.value = true
  importLoading.value = true
  try {
    imports.value = await api.imports(row.id)
  } catch (error) {
    ElMessage.error(error.message)
    imports.value = []
  } finally {
    importLoading.value = false
  }
}

function triggerUpload(row) {
  uploadWellId.value = row.id
  fileInputRef.value?.click()
}

async function handleFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const wellId = uploadWellId.value
  event.target.value = ''
  if (!wellId) return
  try {
    await api.uploadImport(wellId, file)
    ElMessage.success('上传成功')
    await reload()
    if (importDrawerVisible.value && currentImportWellId.value === wellId) {
      imports.value = await api.imports(wellId)
    }
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function runPrediction(wellId, importId = null) {
  try {
    const result = await api.predict(wellId, importId)
    ElMessage.success(`预测完成 #${result.id}`)
    await reload()
    router.push({ name: 'predict', query: { wellId, predictionId: result.id } })
  } catch (error) {
    ElMessage.error(error.message)
  }
}

onMounted(reload)
</script>
