<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { api, ApiError } from '../lib/api'
import type { ImportPreview } from '../lib/types'

const content = ref('')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const preview = ref<ImportPreview | null>(null)
const selectedRows = ref<number[]>([])
const loading = ref(false)
const message = ref('')
const error = ref('')

const selectableRows = computed(() => preview.value?.rows.filter((row) => row.errors.length === 0) ?? [])
const allSelectableRowsSelected = computed(() => selectableRows.value.length > 0 && selectedRows.value.length === selectableRows.value.length)

watch(content, (value) => {
  if (value.trim() && selectedFile.value) {
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
  }
  preview.value = null
  selectedRows.value = []
})

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  preview.value = null
  selectedRows.value = []
  message.value = selectedFile.value ? `已选择：${selectedFile.value.name}` : ''
}

async function previewData() {
  if (!selectedFile.value && !content.value.trim()) {
    error.value = '请粘贴内容或选择 Excel/CSV 文件'
    return
  }
  loading.value = true
  error.value = ''
  message.value = ''
  preview.value = null
  selectedRows.value = []
  try {
    const result = selectedFile.value
      ? await api.upload<ImportPreview>('/api/v1/imports/preview-file', selectedFile.value)
      : await api.post<ImportPreview>('/api/v1/imports/preview', { source_type: 'clipboard', content: content.value })
    preview.value = result
    selectedRows.value = result.rows.filter((row) => row.errors.length === 0).map((row) => row.row_number)
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '解析失败'
  } finally {
    loading.value = false
  }
}

async function commitData() {
  if (!preview.value) return
  if (!selectedRows.value.length) {
    error.value = '至少选择一条有效记录'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const result = selectedFile.value
      ? await api.upload<ImportCommitResult>('/api/v1/imports/commit-file', selectedFile.value, { row_numbers: selectedRows.value.map(String) })
      : await api.post<ImportCommitResult>('/api/v1/imports/commit', { source_type: 'clipboard', content: content.value, row_numbers: selectedRows.value })
    const skippedMessage = result.skipped.length ? `，另有 ${result.skipped.length} 行未选择` : ''
    const warningMessage = result.warnings.length ? `，已确认 ${result.warnings.length} 条重复提示` : ''
    message.value = `已导入 ${result.created_ids.length} 条记录${skippedMessage}${warningMessage}`
    preview.value = null
    selectedRows.value = []
    content.value = ''
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '导入失败'
  } finally {
    loading.value = false
  }
}

function toggleAllSelectableRows() {
  selectedRows.value = allSelectableRowsSelected.value ? [] : selectableRows.value.map((row) => row.row_number)
}

function toggleRow(rowNumber: number, event: Event) {
  const input = event.target
  if (!(input instanceof HTMLInputElement)) return
  if (input.checked && !selectedRows.value.includes(rowNumber)) selectedRows.value = [...selectedRows.value, rowNumber]
  if (!input.checked) selectedRows.value = selectedRows.value.filter((selected) => selected !== rowNumber)
}

interface ImportCommitResult {
  created_ids: string[]
  skipped: Array<{ row_number: number; reason: string; errors: string[]; warnings: string[] }>
  warnings: Array<{ row_number: number; warnings: string[] }>
}
</script>

<template>
  <div class="page-head"><div><h2>批量导入</h2><p>使用确定性规则解析，不做 AI 识别。先预览，再写入正式记录。</p></div><RouterLink class="button" to="/records">返回记录</RouterLink></div>
  <div v-if="error" class="inline-alert">{{ error }}</div>
  <div v-if="message" class="success-alert">{{ message }}</div>
  <div class="import-guide"><div class="guide-box"><strong>只粘贴两列也可以</strong><p>每行按“合作公司 + 项目类型”粘贴，使用 Tab 或逗号分隔。没有日期时自动使用北京时间当天。</p><div class="code-sample">甲公司　DCMM评估<br />乙公司　数据治理咨询</div></div><div class="guide-box"><strong>也支持 Excel / CSV</strong><p>有表头时按列名映射；没有表头时默认前两列是公司和类型，后续列可放日期、绩效和比例。</p><div class="code-sample">合作公司　项目类型　记录日期<br />甲公司　DCMM评估　2026-09-20</div></div></div>
  <div class="card form-card" style="max-width: none"><div class="form-grid"><div class="form-field full"><label>粘贴内容</label><textarea v-model="content" class="textarea import-textarea" placeholder="公司名称    项目类型\n甲公司    DCMM评估\n乙公司    数据治理咨询"></textarea></div><div class="form-field"><label>或选择文件</label><input ref="fileInput" class="input file-input" type="file" accept=".xlsx,.csv,.txt" @change="onFileChange" /></div><div class="form-field file-hint"><label>当前来源</label><span>{{ selectedFile?.name ?? '剪贴板文本' }}</span></div></div><div class="form-footer"><button class="button" :disabled="loading" @click="previewData">{{ loading ? '解析中…' : '预览解析结果' }}</button><button v-if="preview" class="button button-primary" :disabled="loading || !selectedRows.length" @click="commitData">写入 {{ selectedRows.length }} 条已选记录</button></div></div>
  <section v-if="preview" class="card table-card import-preview-card"><div class="section-card-head"><div><h3>解析预览</h3><span>已选 {{ selectedRows.length }} / 有效 {{ preview.valid_count }} · 警告 {{ preview.warning_count }} · 错误 {{ preview.error_count }}</span></div><button class="button button-small" @click="toggleAllSelectableRows">{{ allSelectableRowsSelected ? '取消全选' : '全选有效行' }}</button></div><table class="data-table"><thead><tr><th>导入</th><th>行</th><th>公司</th><th>项目类型</th><th>记录日期</th><th>标准绩效</th><th>个人比例</th><th>校验</th></tr></thead><tbody><tr v-for="row in preview.rows" :key="row.row_number"><td><input type="checkbox" :checked="selectedRows.includes(row.row_number)" :disabled="row.errors.length > 0" :aria-label="`选择第 ${row.row_number} 行`" @change="toggleRow(row.row_number, $event)" /></td><td>{{ row.row_number }}</td><td class="primary-cell">{{ row.company_name || '—' }}</td><td>{{ row.project_type_name || '—' }}</td><td>{{ row.record_date || '—' }}</td><td>{{ row.standard_performance_yuan ?? '使用类型默认' }}</td><td>{{ row.my_ratio_percent ?? '独享100%' }}</td><td><span v-if="row.errors.length" class="error-text">{{ row.errors.join('；') }}</span><span v-else-if="row.warnings.length" class="warning-text">{{ row.warnings.join('；') }}</span><span v-else class="ok-text">可导入</span></td></tr></tbody></table></section>
</template>

<style scoped>
.import-textarea { min-height: 190px; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; line-height: 1.7; }
.file-input { padding: 8px; }
.file-hint span { display: block; padding: 10px 11px; border-radius: 6px; background: #f7f9fb; color: #7f8c9d; font-size: 13px; }
.success-alert { margin-bottom: 14px; padding: 10px 13px; border: 1px solid #c9e7df; border-radius: 6px; background: #f0faf7; color: #27736c; font-size: 12px; }
.import-preview-card { margin-top: 18px; }
.ok-text { color: #2c877c; font-size: 11px; }
</style>
