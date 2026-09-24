<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'
import type { ProjectType, ProjectTypeRule } from '../lib/types'

const { user } = useAuth()
const types = ref<ProjectType[]>([])
const selected = ref<ProjectType | null>(null)
const loading = ref(true)
const error = ref('')
const showTypeForm = ref(false)
const showRuleForm = ref(false)
const submitting = ref(false)
const typeName = ref('')
const ruleForm = reactive({ standard_performance_yuan: '', default_ratio_percent: '100', publicity_required: false, collection_stage: 'none', payout_pattern: 'single', effective_from: new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai' }).format(new Date()), source_note: '' })

const isAdmin = computed(() => user.value?.role === 'admin')
const collectionLabels: Record<string, string> = { none: '无需公司收款节点', advance: '公司预付款', full: '公司全款', advance_and_full: '预付款 + 全款' }
const payoutLabels: Record<string, string> = { single: '一次发放', after_advance: '预付款后发放', advance_then_full: '预付款部分 + 全款尾款', manual: '手工记录' }

async function load() {
  loading.value = true
  try { types.value = await api.get<ProjectType[]>('/api/v1/project-types') } catch (err) { error.value = err instanceof Error ? err.message : '加载失败' } finally { loading.value = false }
}

function choose(type: ProjectType) { selected.value = type }

async function createType() {
  if (!typeName.value.trim()) return
  submitting.value = true
  try { const created = await api.post<ProjectType>('/api/v1/project-types', { name: typeName.value }); types.value.push(created); selected.value = created; typeName.value = ''; showTypeForm.value = false } catch (err) { error.value = err instanceof ApiError ? err.message : '创建失败' } finally { submitting.value = false }
}

async function createRule() {
  if (!selected.value || !ruleForm.standard_performance_yuan) return
  submitting.value = true
  try {
    await api.post<ProjectTypeRule>(`/api/v1/project-types/${selected.value.id}/rules`, { ...ruleForm, standard_performance_yuan: Number(ruleForm.standard_performance_yuan), default_ratio_percent: Number(ruleForm.default_ratio_percent) })
    showRuleForm.value = false
    await load()
    selected.value = types.value.find((item) => item.id === selected.value?.id) ?? null
  } catch (err) { error.value = err instanceof ApiError ? err.message : '保存规则失败' } finally { submitting.value = false }
}

onMounted(load)
</script>

<template>
  <div class="page-head"><div><h2>项目类型</h2><p>价格和结算流程的默认来源。历史记录使用规则快照，不会被后续改价影响。</p></div><button v-if="isAdmin" class="button button-primary" @click="showTypeForm = true">＋ 新建类型</button></div>
  <div v-if="error" class="inline-alert">{{ error }}</div>
  <div class="type-layout">
    <section class="card type-list-card">
      <div class="section-card-head"><h3>类型目录</h3><span>{{ types.length }} 个类型</span></div>
      <div v-if="loading" class="loading-line">正在加载类型…</div>
      <div v-else-if="types.length" class="type-list"><button v-for="type in types" :key="type.id" class="type-list-item" :class="{ selected: selected?.id === type.id }" @click="choose(type)"><span class="type-bullet">{{ type.name.slice(0, 1) }}</span><span><strong>{{ type.name }}</strong><small>{{ type.rules.length ? `已配置 ${type.rules.length} 个版本` : '待配置价格规则' }}</small></span><span class="type-arrow">›</span></button></div>
      <div v-else class="empty-state"><strong>还没有项目类型</strong>{{ isAdmin ? '先创建一个类型，再配置默认绩效。' : '请等待管理员配置项目类型。' }}</div>
    </section>
    <section class="card type-detail-card">
      <template v-if="selected">
        <div class="section-card-head"><div><h3>{{ selected.name }}</h3><span>所有成员共用的默认规则</span></div><button v-if="isAdmin" class="button button-small" @click="showRuleForm = true">＋ 新建规则版本</button></div>
        <div v-if="selected.rules.length"><div v-for="rule in selected.rules" :key="rule.id" class="type-rule"><div class="rule-top"><strong>V{{ rule.version_no }} · ¥{{ rule.standard_performance_yuan.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</strong><span class="status-pill teal">生效自 {{ rule.effective_from }}</span></div><div class="rule-meta"><span>默认比例 {{ rule.default_ratio_percent ?? '待确认' }}%</span><span>{{ rule.publicity_required ? '需要公示' : '无需公示' }}</span><span>{{ collectionLabels[rule.collection_stage] }}</span><span>{{ payoutLabels[rule.payout_pattern] }}</span></div><div v-if="rule.source_note" class="form-help" style="margin-top: 9px">备注：{{ rule.source_note }}</div></div></div>
        <div v-else class="empty-state"><strong>还没有价格规则</strong><span v-if="isAdmin">新建规则后，记录创建时会自动匹配价格和流程。</span></div>
      </template>
      <div v-else class="empty-state"><strong>选择一个项目类型</strong>查看或维护它的绩效和结算规则。</div>
    </section>
  </div>

  <div v-if="showTypeForm" class="drawer-backdrop" @click.self="showTypeForm = false"><aside class="drawer"><div class="drawer-head"><div><div class="eyebrow">PROJECT TYPE</div><h2>新建项目类型</h2></div><button class="close-button" @click="showTypeForm = false">×</button></div><form @submit.prevent="createType"><div class="form-field"><label>类型名称</label><input v-model="typeName" class="input" placeholder="例如：DCMM评估" /></div><div class="form-footer"><button type="button" class="button" @click="showTypeForm = false">取消</button><button class="button button-primary" :disabled="submitting">创建类型</button></div></form></aside></div>
  <div v-if="showRuleForm" class="drawer-backdrop" @click.self="showRuleForm = false"><aside class="drawer"><div class="drawer-head"><div><div class="eyebrow">RULE VERSION</div><h2>新建价格规则</h2></div><button class="close-button" @click="showRuleForm = false">×</button></div><form class="form-grid" @submit.prevent="createRule"><div class="form-field"><label>标准绩效（元）</label><input v-model="ruleForm.standard_performance_yuan" class="input" type="number" min="0" step="0.01" placeholder="例如 8000" /></div><div class="form-field"><label>默认比例（%）</label><input v-model="ruleForm.default_ratio_percent" class="input" type="number" min="0" max="100" step="0.01" /></div><div class="form-field"><label>生效日期</label><input v-model="ruleForm.effective_from" class="input" type="date" /></div><div class="form-field"><label>是否需要公示</label><select v-model="ruleForm.publicity_required" class="select"><option :value="false">不需要公示</option><option :value="true">需要公示</option></select></div><div class="form-field"><label>公司收款节点</label><select v-model="ruleForm.collection_stage" class="select"><option value="none">无需公司收款</option><option value="advance">收到预付款</option><option value="full">收到全款</option><option value="advance_and_full">预付款 + 全款</option></select></div><div class="form-field"><label>个人发放模式</label><select v-model="ruleForm.payout_pattern" class="select"><option value="single">一次发放</option><option value="after_advance">预付款后发放</option><option value="advance_then_full">预付款部分 + 全款尾款</option></select></div><div class="form-field full"><label>规则备注</label><textarea v-model="ruleForm.source_note" class="textarea" placeholder="例如：2026年新标准"></textarea></div><div class="form-footer full"><button type="button" class="button" @click="showRuleForm = false">取消</button><button class="button button-primary" :disabled="submitting">保存规则</button></div></form></aside></div>
</template>

<style scoped>
.type-layout { display: grid; grid-template-columns: 340px minmax(0, 1fr); gap: 17px; }
.type-list-card, .type-detail-card { padding: 21px; }
.type-list { display: grid; gap: 7px; }
.type-list-item { display: grid; grid-template-columns: 32px 1fr 16px; align-items: center; gap: 10px; width: 100%; padding: 12px 10px; border: 1px solid transparent; border-radius: 8px; background: transparent; color: inherit; text-align: left; }
.type-list-item:hover { background: #f7fafb; }
.type-list-item.selected { border-color: #c9e2dd; background: #f0f9f7; }
.type-bullet { display: grid; place-items: center; width: 31px; height: 31px; border-radius: 9px; background: #e7f2f0; color: #2d7d76; font-family: Georgia, serif; }
.type-list-item strong, .type-list-item small { display: block; }
.type-list-item strong { color: #27354b; font-size: 13px; }
.type-list-item small { margin-top: 4px; color: #929eae; font-size: 10px; }
.type-arrow { color: #a3afbd; font-size: 18px; }
</style>
