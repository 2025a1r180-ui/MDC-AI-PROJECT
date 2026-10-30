/**
 * Safety and Crisis Interceptor for Echo Journal (Client-side companion to app/safety.py).
 * Non-Negotiable Rule 1: Echo Journal is a self-reflection tool, NOT a medical or diagnostic system.
 * If an entry or question indicates self-harm or acute psychological crisis,
 * the system suppresses generative inference and surfaces supportive 24/7 helpline resources.
 */

export interface HelplineResource {
  service: string;
  contact: string;
  website: string;
  availability: string;
}

export interface CrisisCheckResult {
  isCrisis: boolean;
  message?: string;
  helplines?: Record<string, HelplineResource>;
  disclaimer?: string;
}

const CRISIS_PATTERNS = [
  /\b(suicid(e|al)|kill myself|end my life|want to die|ending it all)\b/i,
  /\b(self[\s-]?harm|cutting myself|take my own life|slit my wrist)\b/i,
  /\b(better off dead|no reason to live|don'?t want to wake up)\b/i,
];

export const HELPLINE_RESOURCES: Record<string, HelplineResource> = {
  US_Canada: {
    service: 'Suicide & Crisis Lifeline',
    contact: 'Call or Text 988',
    website: 'https://988lifeline.org',
    availability: '24/7, Free and Confidential',
  },
  UK: {
    service: 'Samaritans',
    contact: 'Call 116 123',
    website: 'https://www.samaritans.org',
    availability: '24/7, Free',
  },
  India: {
    service: 'Tele-MANAS / Vandrevala Foundation',
    contact: 'Call 14416 or +91 9999 666 555',
    website: 'https://telemanas.mohfw.gov.in',
    availability: '24/7, Toll-Free',
  },
  International: {
    service: 'International Association for Suicide Prevention (IASP)',
    contact: 'Find a local helpline directory',
    website: 'https://www.iasp.info/resources/Crisis_Centres/',
    availability: 'Global directory of crisis centers',
  },
};

export function checkSafetyClient(text: string): CrisisCheckResult {
  if (!text || !text.trim()) {
    return { isCrisis: false };
  }

  for (const pattern of CRISIS_PATTERNS) {
    if (pattern.test(text)) {
      return {
        isCrisis: true,
        message:
          'It sounds like you may be going through a painful or overwhelming moment. Echo Journal cannot replace real human support and care. Please consider reaching out immediately to someone trained to help:',
        helplines: HELPLINE_RESOURCES,
        disclaimer: 'Echo Journal is a reflective tool, not a crisis or emergency medical provider.',
      };
    }
  }

  return { isCrisis: false };
}
