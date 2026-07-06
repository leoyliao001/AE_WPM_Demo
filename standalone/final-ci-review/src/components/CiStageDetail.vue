<template>
  <section class="stage-detail">
    <header class="stage-detail__head">
      <div>
        <h3 class="stage-detail__title">{{ row.stage }}</h3>
        <p class="stage-detail__sub">{{ row.responsible }} · {{ row.startDate }} → {{ row.endDate }}</p>
      </div>
      <div class="stage-detail__tags">
        <mc-tag
          v-if="row.deadline"
          fit="small"
          :appearance="row.deadline.appearance === 'error' ? 'warning' : 'info'"
          :label="row.deadline.label"
        />
        <mc-tag
          fit="small"
          :appearance="row.status === 'approved' ? 'info' : row.status === 'pending' ? 'warning' : 'neutral'"
          :label="statusLabel(row.status)"
        />
      </div>
    </header>

    <div class="stage-detail__body">
      <template v-if="row.key === 'assessment'">
        <div class="fields">
          <div class="field"><span>Area</span><strong>{{ row.details.area }}</strong></div>
          <div class="field"><span>Requested by</span><strong>{{ row.details.requestedBy }}</strong></div>
          <div class="field field--full"><span>CI comment</span><strong>{{ row.details.comment }}</strong></div>
        </div>
      </template>

      <template v-else-if="row.actionType === 'signoff'">
        <template v-if="detail.signOff.approved">
          <mc-notification appearance="info" fit="small" heading="Sign-off approved">
            {{ detail.signOff.savedComment }}
          </mc-notification>
          <mc-input
            label="Execution Leader recipients"
            placeholder="EL email(s), separated by comma"
            :value="formState.execLeaderRecipients"
            :disabled="detail.signOff.hasEmailSentToEL"
            width="full-width"
            @input="$emit('update:execLeaderRecipients', readValue($event))"
          />
          <p v-if="detail.signOff.hasEmailSentToEL" class="note">
            Email sent on {{ detail.signOff.emailSentToEL }}
          </p>
          <mc-button
            appearance="primary"
            variant="filled"
            fit="small"
            label="Send email to EL"
            icon="mi-envelope"
            :disabled="!canSendElEmail"
            @click="$emit('email-el')"
          />
        </template>
        <template v-else>
          <mc-notification
            v-if="detail.signOff.locked"
            appearance="warning"
            fit="small"
            :heading="detail.signOff.lockMessage"
          />
          <mc-textarea
            label="CI final comments"
            placeholder="Required before approving sign-off"
            :value="formState.ciSignOffComment"
            :disabled="detail.signOff.locked"
            width="full-width"
            @input="$emit('update:ciSignOffComment', readValue($event))"
          />
          <mc-input
            label="Execution Leader recipients"
            placeholder="EL email(s), separated by comma"
            :value="formState.execLeaderRecipients"
            :disabled="detail.signOff.locked"
            width="full-width"
            @input="$emit('update:execLeaderRecipients', readValue($event))"
          />
          <mc-button
            appearance="primary"
            variant="filled"
            fit="small"
            label="Approve sign-off"
            icon="mi-check-circle"
            :disabled="detail.signOff.locked"
            @click="$emit('approve-signoff')"
          />
        </template>
      </template>

      <template v-else-if="row.actionType === 'valueRealized'">
        <template v-if="detail.valueRealized.approved">
          <mc-notification appearance="info" fit="small" heading="Value realised">
            {{ detail.valueRealized.savedComment }}
          </mc-notification>
          <p class="note">PID: <strong>{{ detail.valueRealized.savedPid }}</strong></p>
        </template>
        <template v-else-if="!detail.valueRealized.canMark">
          <mc-notification appearance="neutral" fit="small" :heading="detail.valueRealized.lockMessage" />
        </template>
        <template v-else>
          <mc-input
            label="PID details"
            placeholder="Required"
            :value="formState.elPidDetails"
            width="full-width"
            @input="$emit('update:elPidDetails', readValue($event))"
          />
          <mc-textarea
            label="EL comment / value details"
            placeholder="Describe value captured"
            :value="formState.elComment"
            width="full-width"
            @input="$emit('update:elComment', readValue($event))"
          />
          <mc-button
            appearance="primary"
            variant="filled"
            fit="small"
            label="Mark value realised"
            icon="mi-check-circle"
            @click="$emit('mark-value')"
          />
        </template>
      </template>

      <template v-else-if="row.details?.comment">
        <p class="comment">{{ row.details.comment }}</p>
      </template>
    </div>
  </section>
</template>

<script setup>
defineProps({
  row: { type: Object, required: true },
  detail: { type: Object, required: true },
  formState: { type: Object, required: true },
  canSendElEmail: { type: Boolean, default: false }
})

defineEmits([
  'approve-signoff',
  'email-el',
  'mark-value',
  'update:ciSignOffComment',
  'update:execLeaderRecipients',
  'update:elPidDetails',
  'update:elComment'
])

function readValue(event) {
  return event?.target?.value ?? event?.detail?.value ?? ''
}

function statusLabel(status) {
  if (status === 'approved') return 'Approved'
  if (status === 'pending') return 'Pending'
  return 'Locked'
}
</script>

<style scoped>
.stage-detail {
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(22, 22, 22, 0.04);
  overflow: hidden;
  padding: 20px 22px;
}

.stage-detail__head {
  align-items: flex-start;
  border-bottom: 1px solid rgba(22, 22, 22, 0.06);
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 16px;
}

.stage-detail__title {
  font-size: 17px;
  font-weight: 600;
  margin: 0 0 4px;
}

.stage-detail__sub {
  color: #6c757d;
  font-size: 13px;
  margin: 0;
}

.stage-detail__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stage-detail__body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.fields {
  display: grid;
  gap: 14px;
  grid-template-columns: 1fr 1fr;
}

.field span {
  color: #9aa0a6;
  display: block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.03em;
  margin-bottom: 4px;
  text-transform: uppercase;
}

.field strong {
  font-size: 14px;
  font-weight: 500;
}

.field--full {
  grid-column: 1 / -1;
}

.note,
.comment {
  color: #6c757d;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.comment {
  color: #161616;
}

@media (max-width: 600px) {
  .fields {
    grid-template-columns: 1fr;
  }
}
</style>
