
---

### 1. Voice AI & Telephony Layer
*Costs here are mostly "Pay-as-you-go" based on call duration.*

#### Option A: All-in-One Platforms (Vapi.ai, Retell AI)
*   **Platform Fee:** ~**$0.05 to $0.10 per minute**.
*   **Phone Number:** ~$1.00 - $2.00 per month per number.
*   **Total Estimate:** If a freelancer gets 100 minutes of calls a month, you pay **$10–$15/month** for that user.

#### Option B: Modular Approach (DIY)
*   **Telephony (Twilio):** ~$0.013/min (inbound) + $1.15/month for the phone number.
*   **STT (Deepgram):** ~$0.0043/min.
*   **TTS (ElevenLabs):** This is the expensive part. ~$0.30 per 1,000 characters. In a conversation, this averages to **$0.15–$0.25/min**.
*   **Total Estimate:** Roughly **$0.20–$0.30 per minute**. *Note: While "DIY" sounds cheaper, using premium voices like ElevenLabs actually makes it more expensive than the All-in-One platforms who get bulk discounts.*

---

### 2. Scheduling & Calendar Engine
*This is the "Storage and Logic" for the appointments.*

*   **Nylas:** They have moved toward "Enterprise" pricing. Expect to pay a platform fee (often **$500+/month**) plus a per-account fee (around **$1–$2 per freelancer**). Best for high-security hospital-style needs.
*   **Cronofy:** Similar to Nylas, but slightly more developer-friendly. Pricing is usually custom, but starts around **$0.60 - $1.00 per connected user** per month with a minimum monthly spend.
*   **Cal.com (API):**
    *   **Open Source:** Free (if you self-host on your own server).
    *   **Hosted API:** **$0.05 per booking** or a flat fee per "Atom" (user). This is the most cost-effective for a startup.

---

### 3. The "Brain" (LLM Intelligence)
*This is what the AI uses to think and talk.*

*   **OpenAI (GPT-4o):** Based on tokens (words). A typical 5-minute phone call uses about 2,000–3,000 tokens.
    *   **Cost:** Roughly **$0.01 – $0.03 per call**.
*   **Groq (Llama 3):** If you want speed and lower costs, Groq is significantly cheaper than OpenAI.
    *   **Cost:** Roughly **$0.001 per call** (virtually free at small scales).

---

### 4. Backend & Hosting (The Infrastructure)
*Fixed monthly costs to keep your website and database running.*

*   **Supabase (Database & Auth):**
    *   **Free Tier:** Good for development.
    *   **Pro Tier:** **$25/month** (covers your first few hundred users).
*   **Vercel (Frontend Hosting):**
    *   **Pro Plan:** **$20/month**.
*   **Postmark/Resend (Transactional Emails/receipts):**
    *   **Free** for first 3,000 emails, then **$15/month**.

---

### Summary Cost Table (Per User/Freelancer)

To give you a "Unit Economic" model, here is what it costs you to support **one freelancer** who receives **50 calls a month** (avg 2 mins each = 100 mins total):

| Component | Service Choice | Monthly Cost (Est.) |
| :--- | :--- | :--- |
| **Phone Number** | Twilio/Vapi | $1.15 |
| **Voice Processing** | Vapi.ai (including STT/TTS) | $15.00 |
| **Intelligence** | GPT-4o | $1.50 |
| **Calendar Sync** | Cal.com API | $2.50 |
| **Total Variable Cost** | | **$20.15 / month** |

### Initial Startup "Burn" (Fixed Monthly Costs)
Before you have your first customer, you will likely spend:
*   **Infrastructure (Supabase/Vercel):** $45.00/month.
*   **Development Tools/Domains:** ~$10.00/month.
*   **Total Fixed:** **~$55.00/month.**

### Advice on Pricing your Service:
If your cost is ~$20 per freelancer, you should charge them **$49 to $99 per month**. 
*   **The "Hospital" Value:** Hospitals pay thousands for this. A freelancer will gladly pay $50/month if it saves them from answering the phone while they are working with a client.
*   **Strategy:** Offer a "Lite" plan that is just a dashboard ($15/mo) and a "Pro" plan that includes the AI Receptionist ($50/mo + usage fees).