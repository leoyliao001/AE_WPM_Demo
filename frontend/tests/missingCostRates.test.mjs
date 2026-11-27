import assert from 'node:assert/strict'
import test from 'node:test'
import { parseMissingCostRates } from '../src/utils/missingCostRates.js'

test('extracts distinct missing rate pairs and ignores other financial errors', () => {
  const rates = parseMissingCostRates([
    'Missing 2026 JL2 cost rate for Armenia.',
    'Missing 2026 JL2 cost rate for Armenia.',
    'Missing 2026 JL3 cost rate for Chennai.',
    'Submit Scope with all four job levels locked and a matching final FTE total.'
  ])

  assert.deepEqual(rates, [
    { key: '2026:JL2:Armenia', year: 2026, jobLevel: 'JL2', location: 'Armenia' },
    { key: '2026:JL3:Chennai', year: 2026, jobLevel: 'JL3', location: 'Chennai' }
  ])
})
