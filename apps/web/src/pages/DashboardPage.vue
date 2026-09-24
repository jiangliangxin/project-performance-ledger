<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../lib/api'
import type { DashboardSummary, RecordItem } from '../lib/types'
import StatusPill from '../components/StatusPill.vue'

const summary = ref<DashboardSummary | null>(null)
const records = ref<RecordItem[]>([])
const loading = ref(true)
const error = ref('')

const statusLabels: Record<string, string> = {
  in_progress: '进行中',
  pending_publicity: '待公示',
  pending_advance: '待公司预付款',
  pending_full: '待公司全款',
  pending_ratio: '待确认个人比例',
  pending_payout: '待个人发放',
  pending_first_payout: '待第一批发放',
  partial_paid: '部分发放',
  pending_final_payout: '待尾款发放',
  settled: '已结清',
}

function money(value: number | null | undefined) {
  if (value === null || value === undefined) return '待确认'
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function cents(value: number) {
  return value / 100
}

async function load() {
  loading.value = true
  try {
    const [nextSummary, nextRecords] = await Promise.all([
      api.get<DashboardSummary>('/api/v1/dashboard/summary'),
      api.get<RecordItem[]>('/api/v1/records'),
    ])
    summary.value = nextSummary
    records.value = nextRecords.slice(0, 6)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page-head">
    <div>
      <h2>今天，账本有什么变化？</h2>
      <p>只看真正影响你收益的节点，别让已完成的项目悄悄沉下去。</p>
    </div>
    <div class="actions">
      <RouterLink class="button" to="/imports">批量导入</RouterLink>
      <RouterLink class="button button-primary" to="/records?new=1">＋ 新建记录</RouterLink>
    </div>
  </div>

  <div v-if="loading" class="card loading-line">正在整理你的项目收益…</div>
  <div v-else-if="error" class="card empty-state"><strong>暂时无法加载</strong>{{ error }}</div>
  <template v-else-if="summary">
    <div class="metric-grid">
      <div class="card metric-card">
        <div class="metric-label">合作记录</div>
        <div class="metric-value">{{ summary.project_count }}</div>
        <div class="metric-hint">进行中 {{ summary.in_progress_count }} 条</div>
      </div>
      <div class="card metric-card">
        <div class="metric-label">应得绩效</div>
        <div class="metric-value">{{ money(cents(summary.due_total_cents)) }}</div>
        <div class="metric-hint">已完成 {{ summary.completed_count }} 条</div>
      </div>
      <div class="card metric-card accent">
        <div class="metric-label">已到账</div>
        <div class="metric-value">{{ money(cents(summary.paid_total_cents)) }}</div>
        <div class="metric-hint">按实际到账记录累计</div>
      </div>
      <div class="card metric-card">
        <div class="metric-label">待到账</div>
        <div class="metric-value">{{ money(cents(summary.outstanding_total_cents)) }}</div>
        <div class="metric-hint">待确认金额 {{ summary.unknown_due_count }} 条</div>
      </div>
    </div>

    <div class="dashboard-grid">
      <section class="card section-card">
        <div class="section-card-head">
          <h3>最近需要关注</h3>
          <RouterLink to="/records" class="text-link">查看全部 →</RouterLink>
        </div>
        <div v-if="records.length" class="table-card">
          <table class="data-table">
            <thead><tr><th>合作公司</th><th>项目类型</th><th>当前节点</th><th>待到账</th></tr></thead>
            <tbody>
              <tr v-for="record in records" :key="record.id">
                <td><RouterLink :to="`/records/${record.id}`" class="primary-cell">{{ record.company_name }}</RouterLink></td>
                <td>{{ record.project_type_name }}</td>
                <td><StatusPill :status="record.current_status" :label="record.current_status_label" /></td>
                <td class="money">{{ money(record.outstanding_yuan) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state"><strong>还没有合作记录</strong>从第一条记录开始，把收益沉淀下来。</div>
      </section>

      <section class="card section-card">
        <div class="section-card-head"><h3>账本分布</h3><span>当前数据</span></div>
        <div class="status-list">
          <div v-for="(count, key) in summary.status_counts" :key="key" class="status-row">
            <span>{{ statusLabels[key] ?? key }}</span><strong>{{ count }}</strong>
          </div>
          <div v-if="!Object.keys(summary.status_counts).length" class="empty-state">暂无状态数据</div>
        </div>
        <div class="insight-box" style="margin-top: 17px">
          <strong>记录，而不是猜测</strong>
          <p>公司收款和个人到账分开记录。只要实际到账被记下，账本就会自动更新待到账金额。</p>
        </div>
      </section>
    </div>
  </template>
</template>

<style scoped>
.text-link { color: #31817b; font-size: 12px; }
</style>
