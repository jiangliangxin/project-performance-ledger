<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, ApiError } from '../lib/api'
import type { PerformanceChange, RecordItem } from '../lib/types'
import StatusPill from '../components/StatusPill.vue'

const route = useRoute()
const router = useRouter()
const record = ref<RecordItem | null>(null)
const performanceChanges = ref<PerformanceChange[]>([])
const loading = ref(true)
const error = ref('')
const showPayoutForm = ref(false)
const submitting = ref(false)
const milestoneDate = ref('')
const payoutForm = ref({ amount_yuan: '', received_date: '', batch_type: 'manual', note: '' })
const editForm = ref({ company_name: '', my_ratio_percent: '', override_standard_yuan: '', manual_due_yuan: '', note: '', reason: '' })
const milestoneForm = ref({ completion_date: '', publicity_date: '', advance_received_date: '', full_received_date: '', reason: '' })

const changeLabels: Record<string, string> = {
  ratio: '个人比例',
  standard: '标准绩效',
  due_amount: '个人应得金额',
  completion_date: '完成日期',
  publicity_date: '公示日期',
  advance_received_date: '预付款日期',
  full_received_date: '全款日期',
  payout_amount: '个人到账金额',
  payout_date: '个人到账日期',
  payout_batch: '个人到账批次',
  payout_note: '个人到账备注',
  payout_void: '个人到账作废',
}

const timeline = computed(() => {
  if (!record.value) return []
  const items = [{ label: '记录建立', date: record.value.record_date, done: true }]
  items.push({ label: '工作完成', date: record.value.completion_date ?? '尚未完成', done: record.value.work_status === 'completed' })
  if (record.value.snapshot_publicity_required) items.push({ label: '正式公示', date: record.value.publicity_date ?? '尚未公示', done: record.value.publicity_status === 'published' })
  if (record.value.snapshot_collection_stage === 'advance' || record.value.snapshot_collection_stage === 'advance_and_full') items.push({ label: '公司预付款', date: record.value.advance_received_date ?? '尚未收到', done: Boolean(record.value.advance_received_date) })
  if (record.value.snapshot_collection_stage === 'full' || record.value.snapshot_collection_stage === 'advance_and_full') items.push({ label: '公司全款', date: record.value.full_received_date ?? '尚未收到', done: Boolean(record.value.full_received_date) })
  record.value.payouts.filter((item) => !item.is_void).forEach((payout) => items.push({ label: `个人到账 ¥${payout.amount_yuan.toFixed(2)}`, date: payout.received_date, done: true }))
  return items
})

const collectionLabels: Record<string, string> = { none: '无需公司收款', advance: '预付款', full: '全款', advance_and_full: '预付款 + 全款' }

function money(value: number | null | undefined) {
  if (value === null || value === undefined) return '待确认'
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

async function load() {
  loading.value = true
  try {
    const recordId = String(route.params.id)
    const [loadedRecord, loadedChanges] = await Promise.all([
      api.get<RecordItem>(`/api/v1/records/${recordId}`),
      api.get<PerformanceChange[]>(`/api/v1/records/${recordId}/performance-changes`),
    ])
    record.value = loadedRecord
    performanceChanges.value = loadedChanges
    editForm.value = {
      company_name: loadedRecord.company_name,
      my_ratio_percent: loadedRecord.my_ratio_percent?.toString() ?? '',
      override_standard_yuan: loadedRecord.override_standard_yuan?.toString() ?? '',
      manual_due_yuan: loadedRecord.manual_due_amount_yuan?.toString() ?? '',
      note: loadedRecord.note ?? '',
      reason: '',
    }
    milestoneForm.value = {
      completion_date: loadedRecord.completion_date ?? '',
      publicity_date: loadedRecord.publicity_date ?? '',
      advance_received_date: loadedRecord.advance_received_date ?? '',
      full_received_date: loadedRecord.full_received_date ?? '',
      reason: '',
    }
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function milestone(path: string) {
  try {
    await api.post<RecordItem>(`/api/v1/records/${route.params.id}/${path}`, { occurred_date: milestoneDate.value || null })
    await load()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '更新失败'
  }
}

async function saveEdit() {
  if (!record.value) return
  const nextRatio = editForm.value.my_ratio_percent.trim() ? Number(editForm.value.my_ratio_percent) : null
  const nextStandard = editForm.value.override_standard_yuan.trim() ? Number(editForm.value.override_standard_yuan) : null
  const nextDue = editForm.value.manual_due_yuan.trim() ? Number(editForm.value.manual_due_yuan) : null
  const financialChanged = nextRatio !== record.value.my_ratio_percent
    || nextStandard !== record.value.override_standard_yuan
    || nextDue !== record.value.manual_due_amount_yuan
  if (financialChanged && !editForm.value.reason.trim()) {
    error.value = '调整绩效金额或比例时，请填写调整原因'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    await api.patch<RecordItem>(`/api/v1/records/${record.value.id}`, {
      company_name: editForm.value.company_name,
      my_ratio_percent: nextRatio,
      override_standard_yuan: nextStandard,
      manual_due_yuan: nextDue,
      note: editForm.value.note,
      reason: editForm.value.reason.trim() || null,
    })
    await load()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '保存失败'
  } finally {
    submitting.value = false
  }
}

async function saveMilestones() {
  if (!record.value) return
  if (!milestoneForm.value.reason.trim()) {
    error.value = '更正里程碑日期时，请填写原因'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    await api.patch(`/api/v1/records/${record.value.id}/milestones`, {
      completion_date: milestoneForm.value.completion_date || null,
      publicity_date: milestoneForm.value.publicity_date || null,
      advance_received_date: milestoneForm.value.advance_received_date || null,
      full_received_date: milestoneForm.value.full_received_date || null,
      reason: milestoneForm.value.reason.trim(),
    })
    await load()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '节点日期保存失败'
  } finally {
    submitting.value = false
  }
}

async function savePayout() {
  if (!payoutForm.value.amount_yuan) return
  const amount = Number(payoutForm.value.amount_yuan)
  if (record.value?.outstanding_yuan !== null && record.value?.outstanding_yuan !== undefined
    && amount > record.value.outstanding_yuan
    && !window.confirm(`本次金额超过当前待到账 ${money(record.value.outstanding_yuan)}，仍要记录吗？`)) return
  submitting.value = true
  try {
    await api.post(`/api/v1/records/${route.params.id}/payouts`, {
      amount_yuan: amount,
      received_date: payoutForm.value.received_date || null,
      batch_type: payoutForm.value.batch_type,
      note: payoutForm.value.note || null,
    })
    showPayoutForm.value = false
    payoutForm.value = { amount_yuan: '', received_date: '', batch_type: 'manual', note: '' }
    await load()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '保存到账失败'
  } finally {
    submitting.value = false
  }
}

async function voidPayout(payoutId: string) {
  const reason = window.prompt('请输入作废原因（原记录会保留在历史中）', '原到账信息录入错误')
  if (!reason?.trim()) return
  submitting.value = true
  error.value = ''
  try {
    await api.post(`/api/v1/payouts/${payoutId}/void`, { reason: reason.trim() })
    await load()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '作废到账失败'
  } finally {
    submitting.value = false
  }
}

async function toggleArchive() {
  if (!record.value) return
  const restoring = Boolean(record.value.archived_at)
  if (!restoring && !window.confirm('归档只会将记录从默认列表隐藏，不会改变绩效、节点或到账数据。确定归档吗？')) return
  submitting.value = true
  error.value = ''
  try {
    await api.post(`/api/v1/records/${record.value.id}/${restoring ? 'unarchive' : 'archive'}`)
    await load()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '归档状态更新失败'
  } finally {
    submitting.value = false
  }
}

function historyValue(value: string | null) {
  if (value === null) return '未设置'
  try {
    const parsed: unknown = JSON.parse(value)
    return parsed === null ? '未设置' : String(parsed)
  } catch {
    return value
  }
}

onMounted(load)
</script>

<template>
  <div v-if="loading" class="card loading-line">正在加载合作记录…</div>
  <div v-else-if="error && !record" class="card empty-state"><strong>无法打开记录</strong>{{ error }}<div style="margin-top: 18px"><button class="button" @click="router.back()">返回</button></div></div>
  <template v-else-if="record">
    <div class="page-head"><div><button class="back-link" @click="router.back()">← 返回合作记录</button></div><div class="actions"><button class="button" :disabled="submitting" @click="toggleArchive">{{ record.archived_at ? '恢复到正常列表' : '归档记录' }}</button><input v-model="milestoneDate" class="input milestone-date" type="date" title="不填写则使用北京时间今天" /><button v-if="record.work_status !== 'completed'" class="button" @click="milestone('complete')">标记已完成</button><button v-if="record.snapshot_publicity_required && record.publicity_status !== 'published'" class="button" @click="milestone('publish')">记录已公示</button><button v-if="['advance', 'advance_and_full'].includes(record.snapshot_collection_stage) && !record.advance_received_date" class="button" @click="milestone('advance-received')">记录预付款</button><button v-if="['full', 'advance_and_full'].includes(record.snapshot_collection_stage) && !record.full_received_date" class="button" @click="milestone('full-received')">记录全款</button><button class="button button-primary" @click="showPayoutForm = true">＋ 记录到账</button></div></div>
    <div v-if="error" class="inline-alert">{{ error }}</div>
    <div class="detail-grid">
      <section class="card detail-card">
        <div class="detail-title"><div><h2>{{ record.company_name }}</h2><p>{{ record.project_type_name }} · 记录于 {{ record.record_date }}</p></div><StatusPill :status="record.current_status" :label="record.current_status_label" /></div>
        <div class="metric-grid detail-metrics">
          <div class="metric-card"><div class="metric-label">标准绩效</div><div class="metric-value small">{{ money(record.standard_performance_yuan) }}</div></div>
          <div class="metric-card"><div class="metric-label">我的应得</div><div class="metric-value small">{{ money(record.my_due_amount_yuan) }}</div></div>
          <div class="metric-card accent"><div class="metric-label">已到账</div><div class="metric-value small">{{ money(record.paid_total_yuan) }}</div></div>
          <div class="metric-card"><div class="metric-label">待到账</div><div class="metric-value small">{{ money(record.outstanding_yuan) }}</div></div>
        </div>
        <div class="section-card-head" style="margin-top: 29px"><h3>节点时间线</h3><span>{{ record.snapshot_payout_pattern }}</span></div>
        <div class="timeline"><div v-for="item in timeline" :key="`${item.label}-${item.date}`" class="timeline-item"><div class="timeline-dot" :style="{ opacity: item.done ? 1 : .3 }"></div><div class="timeline-copy"><strong>{{ item.label }}</strong><span>{{ item.date }}</span></div></div></div>
        <div class="section-card-head" style="margin-top: 25px"><h3>更正节点日期</h3><span>留空可撤销该日期；更正会保留历史</span></div>
        <form class="milestone-edit" @submit.prevent="saveMilestones">
          <div class="form-field"><label>完成日期</label><input v-model="milestoneForm.completion_date" class="input" type="date" /></div>
          <div v-if="record.snapshot_publicity_required" class="form-field"><label>公示日期</label><input v-model="milestoneForm.publicity_date" class="input" type="date" /></div>
          <div v-if="['advance', 'advance_and_full'].includes(record.snapshot_collection_stage)" class="form-field"><label>预付款日期</label><input v-model="milestoneForm.advance_received_date" class="input" type="date" /></div>
          <div v-if="['full', 'advance_and_full'].includes(record.snapshot_collection_stage)" class="form-field"><label>全款日期</label><input v-model="milestoneForm.full_received_date" class="input" type="date" /></div>
          <div class="form-field full"><label>更正原因</label><input v-model="milestoneForm.reason" class="input" maxlength="500" placeholder="例如：原日期录入错误，按实际公示材料更正" /></div>
          <div class="form-footer full"><button class="button" :disabled="submitting">保存节点日期</button></div>
        </form>
      </section>

      <aside class="card detail-card">
        <div class="section-card-head"><h3>记录信息</h3><span>{{ record.participation_mode === 'exclusive' ? '独享' : '多人分配' }}</span></div>
        <div class="facts-grid">
          <div class="fact"><label>我的比例</label><strong>{{ record.my_ratio_percent === null ? '待确认' : `${record.my_ratio_percent}%` }}</strong></div>
          <div class="fact"><label>公示要求</label><strong>{{ record.snapshot_publicity_required ? '需要公示' : '不需要公示' }}</strong></div>
          <div class="fact"><label>收款节点</label><strong>{{ collectionLabels[record.snapshot_collection_stage] }}</strong></div>
          <div class="fact"><label>规则来源</label><strong>{{ record.override_reason ? '人工覆盖' : '类型默认' }}</strong></div>
        </div>
        <div class="section-card-head" style="margin-top: 27px"><h3>编辑记录</h3><span>保存后保留调整历史</span></div>
        <form class="form-grid" @submit.prevent="saveEdit">
          <div class="form-field full"><label>合作公司</label><input v-model="editForm.company_name" class="input" /></div>
          <div class="form-field"><label>我的比例</label><input v-model="editForm.my_ratio_percent" class="input" type="number" min="0" max="100" step="0.01" placeholder="待确认" /></div>
          <div class="form-field"><label>人工标准绩效</label><input v-model="editForm.override_standard_yuan" class="input" type="number" min="0" step="0.01" /></div>
          <div class="form-field"><label>人工应得金额</label><input v-model="editForm.manual_due_yuan" class="input" type="number" min="0" step="0.01" /></div>
          <div class="form-field full"><label>绩效调整原因</label><input v-model="editForm.reason" class="input" maxlength="500" placeholder="调整金额或比例时必填" /></div>
          <div class="form-field full"><label>备注</label><textarea v-model="editForm.note" class="textarea"></textarea></div>
          <div class="form-footer full"><button class="button button-primary" :disabled="submitting">保存修改</button></div>
        </form>
      </aside>
    </div>

    <section class="card detail-card payout-section">
      <div class="section-card-head"><h3>个人到账记录</h3><button class="button button-small" @click="showPayoutForm = !showPayoutForm">{{ showPayoutForm ? '取消' : '＋ 新增到账' }}</button></div>
      <div v-if="showPayoutForm" class="payout-form"><div class="form-field"><label>到账金额</label><input v-model="payoutForm.amount_yuan" class="input" type="number" min="0" step="0.01" placeholder="例如 5000" /></div><div class="form-field"><label>到账日期</label><input v-model="payoutForm.received_date" class="input" type="date" /></div><div class="form-field"><label>批次</label><select v-model="payoutForm.batch_type" class="select"><option value="advance">预付款批次</option><option value="final">尾款批次</option><option value="manual">手工记录</option><option value="unknown">待确认批次</option></select></div><div class="form-field payout-note"><label>备注</label><input v-model="payoutForm.note" class="input" placeholder="可选" /></div><button class="button button-primary payout-submit" :disabled="submitting" @click="savePayout">保存</button></div>
      <table v-if="record.payouts.length" class="data-table"><thead><tr><th>到账日期</th><th>批次</th><th>到账金额</th><th>备注</th><th>状态</th><th>操作</th></tr></thead><tbody><tr v-for="payout in record.payouts" :key="payout.id"><td>{{ payout.received_date }}</td><td>{{ payout.batch_type }}</td><td class="money">{{ money(payout.amount_yuan) }}</td><td>{{ payout.note || '—' }}</td><td>{{ payout.is_void ? '已作废' : '有效' }}</td><td><button v-if="!payout.is_void" class="button button-small" :disabled="submitting" @click="voidPayout(payout.id)">作废</button></td></tr></tbody></table>
      <p v-if="record.payouts.length" class="form-help">如需更正到账信息，请作废原记录后新增正确到账；原始到账仍保留在历史中。</p>
      <div v-else class="empty-state">还没有到账记录。公司收款不等于个人到账，请在实际收到绩效后记录。</div>
    </section>

    <section class="card detail-card history-section">
      <div class="section-card-head"><h3>调整历史</h3><span>金额、比例和节点日期更正记录</span></div>
      <table v-if="performanceChanges.length" class="data-table"><thead><tr><th>时间</th><th>调整项</th><th>原值</th><th>新值</th><th>原因</th></tr></thead><tbody><tr v-for="item in performanceChanges" :key="item.id"><td>{{ new Date(item.created_at).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }) }}</td><td>{{ changeLabels[item.field_name] || item.field_name }}</td><td>{{ historyValue(item.old_value) }}</td><td>{{ historyValue(item.new_value) }}</td><td>{{ item.reason }}</td></tr></tbody></table>
      <div v-else class="empty-state">暂时没有金额、比例或节点日期调整记录。</div>
    </section>
  </template>
</template>

<style scoped>
.back-link { border: 0; background: transparent; color: #728197; font-size: 12px; }
.back-link:hover { color: #287e78; }
.detail-metrics { grid-template-columns: repeat(4, 1fr); margin: 0; gap: 9px; }
.detail-metrics .metric-card { min-height: 100px; padding: 14px; }
.detail-metrics .metric-value.small { margin-top: 15px; font-size: 19px; }
.payout-section { margin-top: 18px; padding: 21px; }
.history-section { margin-top: 18px; padding: 21px; }
.payout-form { display: grid; grid-template-columns: 1fr 1fr 1fr 1.4fr auto; align-items: end; gap: 10px; margin-bottom: 18px; padding: 14px; border-radius: 8px; background: #f7fafb; }
.milestone-edit { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 11px; margin-top: 15px; padding: 14px; border-radius: 8px; background: #f7fafb; }
.payout-submit { min-height: 39px; }
.milestone-date { width: 142px; min-height: 37px; padding: 8px; }
@media (max-width: 760px) { .milestone-edit { grid-template-columns: 1fr; } }
</style>
