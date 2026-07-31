<template>
  <PageShell
    title="Migration Chatbot"
    subtitle="Ask questions about migration processes, approvals, risks, and documentation."
    tag="Migration Chatbot"
    back-label="Back to Welcome"
  >
    <section class="chat-layout">
      <div class="chat-panel">
        <div ref="messagesRef" class="chat-messages">
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="chat-bubble"
            :class="`chat-bubble--${msg.role}`"
          >
            <span class="chat-role">{{ msg.role === 'bot' ? 'Assistant' : 'You' }}</span>
            <div v-if="msg.role === 'bot'" class="chat-md" v-html="renderMarkdown(msg.text)" />
            <p v-else>{{ msg.text }}</p>
          </div>
        </div>

        <div class="chat-suggestions">
          <mc-button
            v-for="suggestion in suggestions"
            :key="suggestion"
            appearance="neutral"
            variant="outlined"
            fit="small"
            :label="suggestion"
            @click="askSuggestion(suggestion)"
          />
        </div>

        <div class="chat-input-row">
          <mc-input
            label="Your question"
            hiddenlabel
            placeholder="Type your migration question..."
            width="full-width"
            :value="question"
            @input="onQuestionInput"
            @keydown="onKeydown"
          />
          <mc-button
            appearance="primary"
            variant="filled"
            fit="medium"
            label="Send"
            icon="mi-arrow-right"
            :loading="thinking"
            @click="sendQuestion"
          />
        </div>
      </div>

      <aside class="chat-side">
        <mc-card
          variant="bordered"
          fit="medium"
          heading="Quick tips"
          body="The chatbot can help with intake requirements, approval flows, FTE planning, and risk checklists."
        />
        <mc-card
          variant="bordered"
          fit="medium"
          heading="Data source"
          body="Responses are grounded in the Project Attributes Database and migration playbooks."
        >
          <div slot="image" class="side-icon">
            <mc-icon icon="mi-database" size="24" />
          </div>
        </mc-card>
      </aside>
    </section>
  </PageShell>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import axios from 'axios'
import { marked } from 'marked'
import PageShell from '../components/PageShell.vue'
import { chatbotSuggestions } from '../data/mockData'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-icon'

const suggestions = chatbotSuggestions
const question = ref('')
const thinking = ref(false)
const messagesRef = ref(null)
const messageId = ref(2)

// Conversation history sent to the backend on each request
const chatHistory = ref([])

const messages = ref([
  {
    id: 1,
    role: 'bot',
    text: 'Hello! I can answer questions about migration projects and tasks — status updates, risks, FTE, complexity, and more. What would you like to know?'
  }
])

const renderMarkdown = (text) => marked.parse(text ?? '')

const scrollToBottom = async () => {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

const onQuestionInput = (event) => {
  question.value = event?.target?.value ?? ''
}

const onKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendQuestion()
  }
}

const sendQuestion = async () => {
  const text = question.value.trim()
  if (!text || thinking.value) return

  messages.value.push({ id: messageId.value++, role: 'user', text })
  question.value = ''
  await scrollToBottom()

  thinking.value = true
  try {
    const { data } = await axios.post('/api/migration-chatbot/chat/', {
      question: text,
      history: chatHistory.value
    })
    chatHistory.value.push({ role: 'user', content: text })
    chatHistory.value.push({ role: 'assistant', content: data.answer })
    messages.value.push({ id: messageId.value++, role: 'bot', text: data.answer })
  } catch (error) {
    const msg =
      error?.response?.data?.error ?? 'Unable to get a response. Please try again.'
    messages.value.push({ id: messageId.value++, role: 'bot', text: msg })
  } finally {
    thinking.value = false
    await scrollToBottom()
  }
}

const askSuggestion = (text) => {
  question.value = text
  sendQuestion()
}
</script>

<style scoped>
.chat-layout {
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(0, 1fr) 280px;
}

.chat-panel {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(22, 22, 22, 0.04);
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 520px;
  padding: 20px;
}

.chat-messages {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.chat-bubble {
  border-radius: 12px;
  max-width: 85%;
  padding: 12px 14px;
}

.chat-bubble--bot {
  align-self: flex-start;
  background: rgba(0, 119, 184, 0.08);
}

.chat-bubble--user {
  align-self: flex-end;
  background: rgba(22, 22, 22, 0.06);
}

.chat-role {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: block;
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 4px;
  text-transform: uppercase;
}

.chat-bubble p {
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

/* Markdown content inside bot bubbles */
.chat-md {
  font-size: 14px;
  line-height: 1.6;
}

.chat-md :deep(p) {
  margin: 0 0 8px;
}

.chat-md :deep(p:last-child) {
  margin-bottom: 0;
}

.chat-md :deep(h1),
.chat-md :deep(h2),
.chat-md :deep(h3) {
  font-size: 13px;
  font-weight: 700;
  margin: 12px 0 6px;
  color: #161616;
}

.chat-md :deep(h1:first-child),
.chat-md :deep(h2:first-child),
.chat-md :deep(h3:first-child) {
  margin-top: 0;
}

.chat-md :deep(ul),
.chat-md :deep(ol) {
  margin: 4px 0 8px;
  padding-left: 18px;
}

.chat-md :deep(li) {
  margin-bottom: 3px;
}

.chat-md :deep(table) {
  border-collapse: collapse;
  font-size: 13px;
  margin: 8px 0;
  width: 100%;
}

.chat-md :deep(th) {
  background: rgba(0, 119, 184, 0.1);
  border: 1px solid rgba(0, 119, 184, 0.2);
  font-weight: 600;
  padding: 6px 10px;
  text-align: left;
}

.chat-md :deep(td) {
  border: 1px solid rgba(22, 22, 22, 0.1);
  padding: 5px 10px;
  vertical-align: top;
}

.chat-md :deep(tr:nth-child(even) td) {
  background: rgba(22, 22, 22, 0.02);
}

.chat-md :deep(strong) {
  font-weight: 600;
}

.chat-md :deep(code) {
  background: rgba(22, 22, 22, 0.06);
  border-radius: 3px;
  font-size: 12px;
  padding: 1px 4px;
}

.chat-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chat-input-row {
  align-items: flex-end;
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1fr) auto;
}

.chat-side {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.side-icon {
  color: #0077b8;
  display: flex;
  padding: 4px 0;
}

@media (max-width: 900px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }

  .chat-input-row {
    grid-template-columns: 1fr;
  }
}
</style>
