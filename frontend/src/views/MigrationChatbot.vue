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
            <p>{{ msg.text }}</p>
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

const messages = ref([
  {
    id: 1,
    role: 'bot',
    text: 'Hello! I can help with migration intake, dashboards, approvals, and training planning. What would you like to know?'
  }
])

const botReplies = {
  'What documents are required for a migration request?':
    'You need project name, migration type, region/area, product selection, scope description, language dependency, FTE estimate, and optional risk notes.',
  'How is FTE allocation calculated?':
    'FTE allocation is based on scoping inputs from the intake form and refined during discovery. The Migration Dashboard tracks allocation by site and product.',
  'What are the approval steps before go-live?':
    'Typical steps: Steering Committee → IT Security → Regional Ops sign-off → Final Go-Live approval. See the Approvals milestone for status.',
  'Show me risks for Ocean OPS migration':
    'Key risks: data mapping delays, regional compliance variance, and training readiness. Capture detailed risks in the intake form Risk Assessment section.'
}

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
  await new Promise((resolve) => setTimeout(resolve, 500))

  const reply =
    botReplies[text] ||
    'Thanks for your question. This is a demo chatbot — connect me to the backend API for live migration knowledge base answers.'

  messages.value.push({ id: messageId.value++, role: 'bot', text: reply })
  thinking.value = false
  await scrollToBottom()
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
