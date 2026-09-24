<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, ApiError } from '../lib/api'
import type { ProjectType, RecordItem } from '../lib/types'
import StatusPill from '../components/StatusPill.vue'

const route = useRoute()
const router = useRouter()
const records = ref<RecordItem[]>([])
const projectTypes = ref<ProjectType[]>([])
const loading = ref(true)
const error = ref('')
const search = ref('')
const statusFilter = ref('')
const showArchived = ref(false)
const drawerOpen = ref(false)
const submitting = ref(false)

const defaultDate = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai' }).format(new Date())
const form = reactive({
  company_name: '',
  project_type_id: '',
  record_date: defaultDate(),
  participation_mode: 'exclusive',
  my_ratio_percent: '',
  override_standard_yuan: '',
  override_reason: '',
  note: '',
})

const filteredRecords = computed(() => {
  const query = search.value.trim().toLowerCase()
  return records.value.filter((record) => {
    const matchesQuery = !query || `${record.company_name}${record.project_type_name}`.toLowerCase().includes(query)
    const matchesStatus = !statusFilter.value || record.current_status === statusFilter.value
    return matchesQuery && matchesStatus
  })
})

const statusOptions = [
  ['in_progress', '进行中'],
  ['pending_publicity', '待公示'],
  ['pending_advance', '待公司预付款'],
  ['pending_full', '待公司全款'],
  ['pending_ratio', '待确认个人比例'],
  ['pending_payout', '待个人发放'],
  ['pending_first_payout', '待第一批发放'],
  ['partial_paid', '部分发放'],
  ['pending_final_payout', '待尾款发放'],
  ['settled', '已结清'],
]

function money(value: number | null | undefined) {
  if (value === null || value === undefined) return '待确认'
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function latestRule(type: ProjectType) {
  return type.rules.find((rule) => rule.is_active) ?? type.rules[0]
}

async function load() {
  loading.value = true
  try {
    const [nextRecords, nextTypes] = await Promise.all([
      api.get<RecordItem[]>(`/api/v1/records?archived=${showArchived.value}`),
      api.get<ProjectType[]>('/api/v1/project-types'),
    ])
    records.value = nextRecords
    projectTypes.value = nextTypes.filter((item) => item.status === 'active')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, { company_name: '', project_type_id: '', record_date: defaultDate(), participation_mode: 'exclusive', my_ratio_percent: '', override_standard_yuan: '', override_reason: '', note: '' })
  drawerOpen.value = true
}

function closeCreate() {
  drawerOpen.value = false
  if (route.query.new) router.replace('/records')
}

async function submit() {
  if (!form.company_name.trim() || !form.project_type_id) {
    error.value = '请填写合作公司并选择项目类型'
    return
  }
  if (form.override_standard_yuan && !form.override_reason.trim()) {
    error.value = '填写特殊标准绩效时，请填写调整原因'
    return
  }
  submitting.value = true
  error.value = ''
  const payload = {
    company_name: form.company_name,
    project_type_id: form.project_type_id,
    record_date: form.record_date || null,
    participation_mode: form.participation_mode,
    my_ratio_percent: form.participation_mode === 'shared' && form.my_ratio_percent ? Number(form.my_ratio_percent) : null,
    override_standard_yuan: form.override_standard_yuan ? Number(form.override_standard_yuan) : null,
    override_reason: form.override_reason.trim() || null,
    note: form.note || null,
  }
  try {
    const duplicate = await api.post<{ duplicates: string[]; message: string }>('/api/v1/records/duplicate-check', payload)
    if (duplicate.duplicates.length && !window.confirm(`${duplicate.message}，仍然创建吗？`)) return
    await api.post<RecordItem>('/api/v1/records', payload)
    drawerOpen.value = false
    await load()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '创建失败'
  } finally {
    submitting.value = false
  }
}

async function toggleArchive(record: RecordItem) {
  const restoring = showArchived.value
  if (!restoring && !window.confirm(`确定归档“${record.company_name} · ${record.project_type_name}”吗？归档不会改变绩效和到账记录。`)) return
  try {
    await api.post(`/api/v1/records/${record.id}/${restoring ? 'unarchive' : 'archive'}`)
    await load()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '归档状态更新失败'
  }
}

watch(() => route.query.new, (value) => {
  if (value) openCreate()
}, { immediate: true })

onMounted(load)
</script>

<template>
  <div class="page-head">
    <div><h2>{{ showArchived ? '归档记录' : '合作记录' }}</h2><p>一条记录代表一次合作发生，重复提示但永不自动合并。</p></div>
    <div class="actions"><button class="button" @click="showArchived = !showArchived; load()">{{ showArchived ? '查看正常记录' : '查看归档' }}</button><a v-if="!showArchived" class="button" href="/api/v1/exports/records.csv">导出 CSV</a><a v-if="!showArchived" class="button" href="/api/v1/exports/records.json">导出 JSON</a><RouterLink v-if="!showArchived" class="button" to="/imports">导入数据</RouterLink><button v-if="!showArchived" class="button button-primary" @click="openCreate">＋ 新建记录</button></div>
  </div>

  <div v-if="error" class="inline-alert">{{ error }}</div>
  <div class="filter-row">
    <input v-model="search" class="input search-input" placeholder="搜索公司或项目类型" />
    <select v-model="statusFilter" class="select" style="max-width: 190px"><option value="">全部状态</option><option v-for="option in statusOptions" :key="option[0]" :value="option[0]">{{ option[1] }}</option></select>
    <span class="filter-count">共 {{ filteredRecords.length }} 条</span>
  </div>

  <div class="card table-card">
    <div v-if="loading" class="loading-line">正在加载记录…</div>
    <table v-else-if="filteredRecords.length" class="data-table">
      <thead><tr><th>合作公司</th><th>项目类型</th><th>记录日期</th><th>当前节点</th><th>应得绩效</th><th>已到账</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="record in filteredRecords" :key="record.id">
          <td><RouterLink :to="`/records/${record.id}`" class="primary-cell">{{ record.company_name }}</RouterLink></td>
          <td>{{ record.project_type_name }}</td>
          <td>{{ record.record_date }}</td>
          <td><StatusPill :status="record.current_status" :label="record.current_status_label" /></td>
          <td class="money">{{ money(record.my_due_amount_yuan) }}</td>
          <td class="money">{{ money(record.paid_total_yuan) }}</td>
          <td class="row-actions"><RouterLink :to="`/records/${record.id}`" class="button button-small">查看</RouterLink><button class="button button-small" @click="toggleArchive(record)">{{ showArchived ? '恢复' : '归档' }}</button></td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty-state"><strong>{{ showArchived ? '没有归档记录' : '还没有合作记录' }}</strong>{{ showArchived ? '归档只整理列表，不删除历史数据。' : '只需要公司、类型和日期，就可以开始记录。' }}<div v-if="!showArchived" style="margin-top: 17px"><button class="button button-primary" @click="openCreate">新建第一条</button></div></div>
  </div>

  <div v-if="drawerOpen" class="drawer-backdrop" @click.self="closeCreate">
    <aside class="drawer">
      <div class="drawer-head"><div><div class="eyebrow">NEW COOPERATION RECORD</div><h2>新建合作记录</h2></div><button class="close-button" @click="closeCreate">×</button></div>
      <p class="drawer-intro">先记下合作公司和项目类型，剩余节点可以在后续发生时补录。</p>
      <form class="form-grid" @submit.prevent="submit">
        <div class="form-field full"><label>合作公司 <span class="required">*</span></label><input v-model="form.company_name" class="input" placeholder="例如：甲公司" /></div>
        <div class="form-field full"><label>项目类型 <span class="required">*</span></label><select v-model="form.project_type_id" class="select"><option value="">选择项目类型</option><option v-for="type in projectTypes" :key="type.id" :value="type.id">{{ type.name }}{{ latestRule(type) ? ` · ¥${latestRule(type).standard_performance_yuan}` : '' }}</option></select><span v-if="!projectTypes.length" class="form-help">请先让管理员在“项目类型”中创建规则。</span></div>
        <div class="form-field"><label>记录日期</label><input v-model="form.record_date" class="input" type="date" /><span class="form-help">默认使用北京时间当前日期。</span></div>
        <div class="form-field"><label>参与方式</label><select v-model="form.participation_mode" class="select"><option value="exclusive">独享（默认100%）</option><option value="shared">多人分配</option></select></div>
        <div v-if="form.participation_mode === 'shared'" class="form-field"><label>我的比例（可后补）</label><div class="inline-field"><input v-model="form.my_ratio_percent" class="input" type="number" min="0" max="100" step="0.01" placeholder="例如 30" /><span>%</span></div></div>
        <div class="form-field"><label>特殊标准绩效（可选）</label><input v-model="form.override_standard_yuan" class="input" type="number" min="0" step="0.01" placeholder="默认使用项目类型价格" /></div>
        <div v-if="form.override_standard_yuan" class="form-field full"><label>调整原因 <span class="required">*</span></label><input v-model="form.override_reason" class="input" maxlength="500" placeholder="例如：客户特殊约定" /></div>
        <div class="form-field full"><label>备注</label><textarea v-model="form.note" class="textarea" placeholder="记录需要特别说明的情况"></textarea></div>
        <div class="form-footer full"><button type="button" class="button" @click="closeCreate">取消</button><button class="button button-primary" :disabled="submitting">{{ submitting ? '保存中…' : '保存记录' }}</button></div>
      </form>
    </aside>
  </div>
</template>

<style scoped>
.filter-count { color: #9aa5b5; font-size: 12px; }
.inline-alert { margin-bottom: 14px; padding: 10px 13px; border: 1px solid #f1d2d0; border-radius: 6px; background: #fff5f4; color: #a44e53; font-size: 12px; }
.drawer-intro { margin: -8px 0 22px; color: #8190a2; font-size: 12px; line-height: 1.7; }
.required { color: #bb5f64; }
.row-actions { display: flex; gap: 6px; align-items: center; }
</style>
