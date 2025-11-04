from flask import Flask, render_template, redirect, url_for, request, session
import re
from pathlib import Path
import markdown

app = Flask(__name__)
app.secret_key = 'freight-training-secret-key-2025'  # Required for session management

PROJECT_MD_PATH = Path(__file__).parent / "project.md"

# Quiz questions for Module 1.1
MODULE_1_1_QUIZ = [
    {
        "id": "q1_1_1",
        "question": "A potential customer asks why they should work with you instead of calling carriers directly. Which response best demonstrates your value proposition?",
        "choices": [
            "I can get you the cheapest rate possible every time",
            "I provide access to a network of carriers, handle logistics complexities, verify credentials, and save you time so you can focus on your core business",
            "I just pass along shipment information to carriers and collect a fee",
            "I only work with one exclusive carrier that gives the best service"
        ],
        "correct_index": 1,
        "explanation": "Your value proposition includes expertise, carrier network access, time savings, risk management through credential verification, and allowing customers to focus on their core business. You're a logistics consultant, not just a middleman or someone who only promises the cheapest rates."
    },
    {
        "id": "q1_1_2",
        "question": "Approximately what percentage of all freight tonnage in the United States moves by truck, and why does this matter to you as a freight agent?",
        "choices": [
            "50% - meaning trucking is one of several equally important freight methods",
            "70% - demonstrating that trucking is essential to the economy and your services facilitate critical operations",
            "30% - showing that most freight moves by rail and ship instead",
            "90% - proving that all other shipping methods are obsolete"
        ],
        "correct_index": 1,
        "explanation": "Approximately 70% of all freight tonnage moves by truck, making trucking essential to the American economy. This means the services you provide aren't optional extras—you're facilitating critical operations that businesses depend on."
    }
]

# Quiz questions for Module 1.2
MODULE_1_2_QUIZ = [
    {
        "id": "q1_2_1",
        "question": "The trucking industry generates approximately how much in annual revenue, and what does this scale mean for your career?",
        "choices": [
            "$200 billion - indicating a small, specialized market with limited opportunities",
            "$800+ billion - demonstrating a massive industry with substantial career opportunities",
            "$8 trillion - showing trucking is the largest industry in America",
            "$80 billion - suggesting a moderate-sized niche market"
        ],
        "correct_index": 1,
        "explanation": "The trucking industry generates over $800 billion in annual revenue, demonstrating a massive industry with substantial career opportunities. This scale shows there's significant room for successful freight agents who provide valuable services."
    }
]

# Quiz questions for Module 1.3
MODULE_1_3_QUIZ = [
    {
        "id": "q1_3_1",
        "question": "A shipper tells you they can get a load moved for $1,500 by calling a carrier directly. You can arrange it for $1,200 with a $300 commission. What should you emphasize in your response?",
        "choices": [
            "You should drop your commission to compete on price alone",
            "They save $300, you earn your commission, and the carrier gets a fair rate—everyone wins, plus they get your expertise and service",
            "Tell them to use the carrier directly since they found a better price",
            "Explain that your $1,500 price is actually better because it includes hidden fees they don't know about"
        ],
        "correct_index": 1,
        "explanation": "This is a perfect example of creating value for everyone. The shipper saves money ($300), you earn your commission ($300), and the carrier receives a fair rate. Plus, the shipper gets your expertise, carrier network access, and risk management—demonstrating that using a freight agent often provides better pricing along with superior service."
    },
    {
        "id": "q1_3_2",
        "question": "Which of the following best describes how you provide 'Risk Management' value to your customers?",
        "choices": [
            "You insure every shipment personally against damage or loss",
            "You verify carrier credentials, ensure proper insurance coverage, and help resolve issues—protecting clients from risks they might not know exist",
            "You only work with the three largest carriers to eliminate all risk",
            "You guarantee that nothing will ever go wrong with any shipment"
        ],
        "correct_index": 1,
        "explanation": "Risk management means verifying carrier credentials, ensuring proper insurance coverage, and helping resolve issues when problems arise. This due diligence protects your clients from risks they might not even know exist, such as working with carriers who have inadequate insurance or poor safety records."
    }
]

# Quiz questions for Module 1.4
MODULE_1_4_QUIZ = [
    {
        "id": "q1_4_1",
        "question": "You arrange a shipment where the customer pays $2,000 and the carrier receives $1,600, creating a $400 gross margin. With your compensation structure, what do you earn from this transaction?",
        "choices": [
            "You earn the full $2,000 customer payment",
            "You earn your base salary plus commission on the $400 margin",
            "You earn $400 total with no additional salary",
            "You earn a percentage of the $2,000 total revenue"
        ],
        "correct_index": 1,
        "explanation": "You earn your base salary plus commission on the $400 gross margin (the difference between what the customer pays and what the carrier receives). Your compensation structure provides income stability through base salary while rewarding performance through commissions on the margins you generate."
    },
    {
        "id": "q1_4_2",
        "question": "What is the key advantage of the salaried-plus-commission compensation structure compared to pure commission?",
        "choices": [
            "You make more total money with a salary than with pure commission",
            "You never have to work hard because the salary covers everything",
            "Your base salary provides financial stability while you build your customer base, removing the stress of variable income during the learning phase",
            "The commission is just a bonus and doesn't really matter to your income"
        ],
        "correct_index": 2,
        "explanation": "The base salary provides financial stability while you develop your book of business, removing the financial stress that purely commission-based roles create. This allows you to focus on building long-term relationships rather than desperate short-term tactics, while commission earnings reward your effectiveness and grow as you become more successful."
    }
]

# Quiz questions for Module 1.5
MODULE_1_5_QUIZ = [
    {
        "id": "q1_5_1",
        "question": "You're in Month 2 of your freight agent career. You've made very few shipments and commission earnings are minimal. What should be your primary focus and mindset?",
        "choices": [
            "Quit immediately because low earnings in Month 2 means you'll never succeed",
            "Focus on learning, mastering systems, and building your prospecting foundation—minimal commission during months 1-3 is normal and expected",
            "Pressure every prospect to book immediately to generate quick income",
            "Spend all your time looking for a different career",
        ],
        "correct_index": 1,
        "explanation": "During months 1-3 (Foundation Building phase), your focus should be on learning rather than earning. You'll spend significant time in training, studying industry practices, understanding systems, and developing prospecting skills. Your salary provides financial stability during this essential learning period. Minimal commission earnings during this phase are normal and expected."
    },
    {
        "id": "q1_5_2",
        "question": "During months 6-12 of your career, what key shift typically occurs that drives increased commission earnings?",
        "choices": [
            "You suddenly learn secret pricing techniques that double your margins",
            "Your earlier customers begin providing repeat business, your efficiency improves, and you have more time for business development as efforts compound",
            "The company automatically assigns you bigger customers",
            "Market conditions always improve during this timeframe"
        ],
        "correct_index": 1,
        "explanation": "During the Momentum Building phase (months 6-12), your efforts compound. Customers you secured earlier begin providing repeat business, your operational efficiency improves allowing more time for business development, commission earnings become more substantial as shipment volume increases and pricing skills sharpen. This is the natural result of consistent effort over time."
    },
    {
        "id": "q1_5_3",
        "question": "'The prospecting calls you make today produce customers 30-90 days from now.' What critical principle does this statement teach you?",
        "choices": [
            "You should wait 90 days before making any prospecting calls",
            "Effort precedes results—consistent daily activity is essential even when immediate results aren't visible",
            "Prospecting doesn't work until you've been in the business for 90 days",
            "You only need to prospect once every 30-90 days"
        ],
        "correct_index": 1,
        "explanation": "This illustrates the principle that effort precedes results. Your current income reflects efforts from previous months, not today's work. This means you must maintain consistent daily prospecting activity even when you don't see immediate results, because those efforts will produce customers and revenue 30-90 days in the future."
    }
]

# Quiz questions for Module 1.6
MODULE_1_6_QUIZ = [
    {
        "id": "q1_6_1",
        "question": "A shipment you arranged is running late due to carrier delays. The customer hasn't called yet. What does professionalism require you to do?",
        "choices": [
            "Wait for the customer to call and complain, then explain it's the carrier's fault",
            "Communicate proactively about the delay before they call, own the situation, and provide updates on resolution",
            "Ignore it and hope the customer doesn't notice",
            "Blame the carrier and tell the customer to contact them directly"
        ],
        "correct_index": 1,
        "explanation": "Professionalism requires proactive communication. When a shipment is running late, communicate proactively rather than waiting for angry phone calls. Own the situation, provide clear information, and update on resolution efforts. This builds trust even when problems occur, whereas hiding issues or deflecting blame destroys your reputation."
    },
    {
        "id": "q1_6_2",
        "question": "You can book a problematic load that you know will likely have issues, earning a quick $400 commission. What should you do?",
        "choices": [
            "Book it immediately—$400 is $400, and it's the customer's problem if issues arise",
            "Don't book loads you know are problematic just to earn commission—always act in your customer's best interest even when it costs you money short-term",
            "Book it but don't tell the customer about the potential problems",
            "Book it and blame any problems on the carrier later"
        ],
        "correct_index": 1,
        "explanation": "Ethical behavior means always acting in your customer's best interest, even when it costs you money in the short term. Don't book loads you know are problematic just to earn a commission. Ethical lapses might create short-term profits but destroy long-term success. Your reputation is your most valuable asset."
    },
    {
        "id": "q1_6_3",
        "question": "Why is treating everyone with respect—including small customers and every carrier—described as a 'strategic business decision' rather than just 'being nice'?",
        "choices": [
            "It's not strategic; it's just about being a good person with no business impact",
            "Small customers today may become large customers tomorrow; carriers you treat well will prioritize your freight when capacity is tight; reputation drives success in this relationship-based industry",
            "You're legally required to treat everyone equally by federal regulation",
            "It only matters for large customers; small customers and carriers don't impact your success"
        ],
        "correct_index": 1,
        "explanation": "Professionalism is a strategic business decision because relationships and reputation drive success in this industry. Small customers today might become large customers tomorrow. Carriers you treat well and pay promptly will prioritize your freight when capacity is tight. Drivers you respect will remember and accept your loads in the future. Your reputation is your competitive advantage."
    }
]

# Quiz questions for Module 2.1
MODULE_2_1_QUIZ = [
    {
        "id": "q2_1_1",
        "question": "A customer asks for a rush shipment and questions why the rate is higher than usual. How do you best explain this using your knowledge of the freight ecosystem?",
        "choices": [
            "Suggest they wait until rates go down next week",
            "Offer to find a cheaper carrier even if it means lower service quality",
            "Explain that tight capacity affects carriers who then demand premium rates, and you must pass those costs along—helping them understand market realities",
            "Tell them that's just how pricing works during busy times"
        ],
        "correct_index": 2,
        "explanation": "Understanding the ecosystem helps you educate customers about market realities. When capacity is tight, carriers can be selective and demand higher rates. Explaining this transforms you from someone who 'just quotes prices' into a consultant who helps customers understand the business dynamics affecting their shipping costs."
    },
    {
        "id": "q2_1_2",
        "question": "Why is understanding the freight ecosystem compared to 'understanding a city' in the training material?",
        "choices": [
            "Because cities are the only places where freight agents work",
            "Because freight only moves within cities, not between them",
            "Because both involve driving trucks through streets",
            "Just like knowing a city's neighborhoods helps you navigate effectively, knowing who the industry participants are and how they interact makes you more effective at solving logistics problems"
        ],
        "correct_index": 3,
        "explanation": "The analogy emphasizes that understanding the structure and relationships within the freight industry—who does what, how they interact, where you fit—makes you far more effective. You could operate without this knowledge, but understanding the ecosystem transforms you from a basic service provider into a knowledgeable consultant who can educate customers and navigate complex situations."
    }
]

# Quiz questions for Module 2.2
MODULE_2_2_QUIZ = [
    {
        "id": "q2_2_1",
        "question": "You're approaching a large manufacturer who has established carrier relationships. What's your best strategy?",
        "choices": [
            "Position yourself as their capacity supplement for peak seasons and backup situations when regular carriers are full",
            "Tell them their current carriers are probably unreliable",
            "Undercut their current carriers' rates by 30% to win the business",
            "Demand they give you all their freight immediately to prove your value"
        ],
        "correct_index": 0,
        "explanation": "Manufacturers have established relationships built over years. Trying to replace their primary carriers creates resistance. Instead, position yourself as a capacity supplement for peak seasons and backup situations. This reduces resistance and creates win-win opportunities where you provide value without threatening their existing relationships."
    }
]

# Quiz questions for Module 2.3
MODULE_2_3_QUIZ = [
    {
        "id": "q2_3_1",
        "question": "When should you use an owner-operator versus a large national carrier?",
        "choices": [
            "It doesn't matter—all carriers are the same",
            "Always use large carriers because they're safer",
            "Only use owner-operators because they're cheaper",
            "Use owner-operators for loads requiring special attention or white-glove service where you've built trust; use large carriers for high-volume customers requiring significant capacity"
        ],
        "correct_index": 3,
        "explanation": "Different carrier types serve different needs. Owner-operators often provide excellent personalized service for special-attention loads, especially on lanes where you've built relationships. Large national carriers offer capacity, geographic reach, and sophisticated systems for high-volume customers. Matching carrier type to shipment requirements is a key skill."
    }
]

# Quiz questions for Module 2.4
MODULE_2_4_QUIZ = [
    {
        "id": "q2_4_1",
        "question": "A freight forwarder contacts you about domestic trucking for an international shipment. What opportunity does this represent?",
        "choices": [
            "Forwarders only handle air freight, not trucking",
            "No opportunity—forwarders are competitors, not customers",
            "You should only work with direct shippers, never intermediaries",
            "Drayage movements (first and last mile) from shipper to port or port to final destination"
        ],
        "correct_index": 3,
        "explanation": "Freight forwarders specialize in international shipping but often need domestic trucking for first and last miles—moving freight from the shipper to the port, or from the port to the final destination. These 'drayage' movements create opportunities for freight agents who understand intermodal operations."
    }
]

# Quiz questions for Module 2.5
MODULE_2_5_QUIZ = [
    {
        "id": "q2_5_1",
        "question": "Before tendering a load to a carrier you found on a load board, what must you verify?",
        "choices": [
            "Active FMCSA authority, valid insurance at required levels, and acceptable safety ratings",
            "Nothing—if they're on the load board, they're automatically qualified",
            "Only that they have a truck available",
            "Just their phone number and company name"
        ],
        "correct_index": 0,
        "explanation": "Federal regulations require brokers to verify that carriers have proper authority, insurance, and acceptable safety ratings before tendering freight. This includes active FMCSA operating authority, valid commercial auto liability insurance at required levels ($750K minimum for most freight), and acceptable safety ratings. Using carriers without proper credentials exposes you to enormous liability."
    }
]

# Quiz questions for Module 2.6
MODULE_2_6_QUIZ = [
    {
        "id": "q2_6_1",
        "question": "Your customer pays net 30 terms, but the carrier expects payment in 7 days. You haven't received customer payment yet. What should you do?",
        "choices": [
            "Negotiate with the carrier to accept net 30 terms too",
            "Tell the carrier they have to wait for the customer to pay first",
            "Pay the carrier according to your agreed terms (net 7)—your obligation exists regardless of when customers pay you",
            "Wait to pay the carrier until after the customer pays you"
        ],
        "correct_index": 2,
        "explanation": "The timing mismatch between customer payments (net 30) and carrier expectations (net 7) is normal in freight brokerage. Your obligation to pay carriers exists independently of when customers pay you. Paying carriers according to agreed terms builds relationships—carriers who aren't paid on time will stop accepting your loads and warn others about you."
    }
]

# Quiz questions for Module 2.7
MODULE_2_7_QUIZ = [
    {
        "id": "q2_7_1",
        "question": "It's mid-September, and a customer asks why rates have increased 20% compared to last month. What's the most likely explanation?",
        "choices": [
            "Pre-holiday season tight capacity as retailers stock shelves for holiday shopping—more loads than available trucks drives rates up",
            "Summer is ending so rates always increase in fall",
            "Carriers are price gouging for no reason",
            "Your brokerage increased fees without telling you"
        ],
        "correct_index": 0,
        "explanation": "September through early November sees tight capacity as retailers stock shelves for holiday shopping. This seasonal pattern creates more loads than available trucks, allowing carriers to be selective and demand higher rates. Understanding these predictable patterns helps you price appropriately and educate customers about market conditions rather than seeming arbitrary."
    }
]

# Quiz questions for Module 2.8
MODULE_2_8_QUIZ = [
    {
        "id": "q2_8_1",
        "question": "A small customer says a large national brokerage like C.H. Robinson quoted them a lower rate. How should you respond?",
        "choices": [
            "Tell them large brokerages provide terrible service",
            "Give up—you can't compete with large brokerages",
            "Emphasize your personal service, faster response times, flexibility, and direct customer relationships—you're their personal logistics advisor",
            "Match their rate exactly even if it means no profit for you"
        ],
        "correct_index": 2,
        "explanation": "Large brokerages have advantages in buying power and technology, but often provide bureaucratic, slow, inconsistent service where customers feel like small fish in a big pond. Your competitive advantage is personal service, faster response times, flexibility, and direct relationships. Position yourself as the 'personal logistics advisor' rather than competing on price or scale."
    }
]

# Quiz questions for Module 2.9
MODULE_2_9_QUIZ = [
    {
        "id": "q2_9_1",
        "question": "You have a background working in food manufacturing. How might this influence your niche selection?",
        "choices": [
            "Keep it secret from customers so they think you're objective",
            "Only work with construction companies to diversify away from your background",
            "It's irrelevant—avoid food industry freight because you know it too well",
            "Specialize in food and beverage freight—your background provides instant credibility and understanding of temperature requirements, food safety regulations, and industry needs"
        ],
        "correct_index": 3,
        "explanation": "Previous work experience in an industry provides instant credibility and understanding. Your food manufacturing background gives you knowledge of temperature requirements, food safety regulations, food-grade trailer specifications, and industry terminology. This expertise commands premium pricing and helps you build relationships faster than generalist competitors."
    }
]

# Chapter 3 Quizzes
chapter3_quizzes = [
    {
        "id": "q3_1_1",
        "question": "A customer calls with an urgent operational issue while you're in the middle of a prospecting call with a promising new lead. What should you do?",
        "choices": [
            "Finish the prospecting call first since new business is the lifeblood of your operation",
            "Excuse yourself from the prospecting call, handle the customer's urgent issue immediately, then call the prospect back later",
            "Let the customer's call go to voicemail and follow up after the prospecting call",
            "Ask the customer to email you the details while you finish the sales call"
        ],
        "correct_index": 1,
        "explanation": "Active shipments and customer service always take priority over sales activities. Operational issues require immediate attention because failing to manage them properly damages relationships with both customers and carriers. You can reschedule prospecting calls, but you can't recover from service failures."
    },
    {
        "id": "q3_2_1",
        "question": "A prospect who ships 40 loads monthly tells you they'll only work with you if you match rates that are 25% below current market conditions. How should you respond?",
        "choices": [
            "Accept their terms to secure the high-volume account and hope to increase rates later",
            "This prospect isn't qualified—politely explain your rates reflect market conditions and move on to better prospects",
            "Agree to their rates but provide minimal service to protect your margins",
            "Counter-offer at 20% below market instead of 25%"
        ],
        "correct_index": 1,
        "explanation": "Qualifying means determining whether a prospect is genuinely worth pursuing. A company demanding rates 25% below market isn't qualified regardless of volume. Quality matters more than quantity. Working at unsustainable margins creates a cycle of working hard for minimal income and eventual business failure."
    },
    {
        "id": "q3_2_2",
        "question": "You're presenting your services to a logistics manager who mentions they're frustrated by poor communication from their current provider. What's the most effective approach?",
        "choices": [
            "Provide a generic overview of all your company's services and capabilities",
            "Immediately quote lower rates than their current provider",
            "Connect directly to their specific concern: 'Communication is critical. Here's exactly how I'll keep you updated proactively at every stage of the shipment—pickup confirmation, mid-transit updates, and delivery confirmation—so you never wonder where your freight is.'",
            "Tell them your brokerage has the best technology in the industry"
        ],
        "correct_index": 2,
        "explanation": "Effective presenting means connecting your services directly to the prospect's specific situation. When they mention poor communication as their pain point, address that concern specifically with concrete examples of how you'll solve that problem. Generic presentations about how great your company is rarely work."
    },
    {
        "id": "q3_3_1",
        "question": "A customer says they need to ship '25,000 lbs of parts from Dallas to Atlanta next Tuesday.' What's your next step?",
        "choices": [
            "Immediately post this on a load board to find available carriers",
            "Quote them a rate based on typical Dallas-Atlanta pricing",
            "Gather complete load details: specific pickup and delivery addresses, appointment times, exact commodity, dimensions, piece count, special requirements, and contact information",
            "Ask if they prefer dry van or flatbed equipment"
        ],
        "correct_index": 2,
        "explanation": "Every shipment requires specific information before you can price it accurately and find an appropriate carrier. General terms like 'parts' aren't sufficient. Missing or incorrect details cause problems later. Complete information gathering is the essential first step in load booking."
    },
    {
        "id": "q3_3_2",
        "question": "You book a load from a customer for $1,800. To preserve healthy margins, you want to pay the carrier no more than $1,300. Which factor should be LEAST important in determining if this carrier rate is realistic?",
        "choices": [
            "How much commission you personally want to earn",
            "Current market rates for this specific lane",
            "Difficulty factors like rural locations or tight appointment times",
            "Seasonal capacity conditions in the market"
        ],
        "correct_index": 0,
        "explanation": "While your desired margin matters, pricing should primarily reflect real market conditions and the difficulty of the shipment. Current market rates, lane difficulty, urgency, and capacity conditions should drive your carrier rate expectations. Unrealistic carrier rates based solely on what you want to earn won't attract quality carriers and will cause service failures."
    },
    {
        "id": "q3_4_1",
        "question": "You receive a call from a driver who says he'll be 45 minutes late to a delivery appointment due to an unexpected traffic delay. The customer's receiving hours close in one hour. What should you do first?",
        "choices": [
            "Tell the driver to do his best and hope he makes it on time",
            "Wait to see if the driver actually delivers late before contacting the customer",
            "Immediately call the customer, explain the situation, and ask if they can stay open an extra 30 minutes to accommodate the delay",
            "Document the delay in your TMS system for your records"
        ],
        "correct_index": 2,
        "explanation": "Proactive communication before problems become crises is essential. Contact the customer immediately to explain the situation and propose solutions. This gives them time to adjust their schedule and shows you're managing the situation attentively. Waiting until after a problem occurs damages trust and eliminates options for resolution."
    },
    {
        "id": "q3_4_2",
        "question": "Three months after delivery, a customer disputes a $150 detention charge on an invoice. They claim the driver wasn't delayed. What's your best course of action?",
        "choices": [
            "Immediately waive the charge to maintain the customer relationship",
            "Refuse to discuss it since three months have passed",
            "Gather all relevant documentation (BOL, POD, rate confirmation, detention documentation, timestamps) to understand what actually happened, then make a fair decision based on facts",
            "Tell the customer it's the carrier's fault, not yours"
        ],
        "correct_index": 2,
        "explanation": "Dispute resolution requires gathering all relevant documentation to determine what's fair based on facts. Sometimes the customer is right, sometimes the carrier is right, and sometimes both parties share responsibility. Make decisions based on documentation and facts, not on assumptions or expediency."
    },
    {
        "id": "q3_5_1",
        "question": "A carrier you've worked with successfully on five previous loads completes a delivery on Friday. Your payment terms with carriers are net 15 days. Your customer hasn't paid you yet and likely won't pay for 25 days. When should you pay the carrier?",
        "choices": [
            "Wait until you receive payment from the customer first",
            "Pay the carrier in 15 days as agreed, regardless of whether the customer has paid you",
            "Explain to the carrier that payment will be delayed until the customer pays",
            "Offer to pay in 30 days instead since that's more convenient for your cash flow"
        ],
        "correct_index": 1,
        "explanation": "Pay carriers according to agreed terms regardless of whether customers have paid you. Your obligation to carriers exists independently of whether you've been paid. Late payment damages relationships severely. Carriers who aren't paid on time will stop accepting your loads, and word spreads through the carrier community about agents who don't pay fairly or promptly."
    },
    {
        "id": "q3_5_2",
        "question": "You notice that a customer consistently provides good volume (12-15 loads monthly) but the margins average only 8% compared to your typical 18% margins. What should you consider before deciding whether to continue the relationship?",
        "choices": [
            "Immediately stop working with them since 8% margins are unacceptable",
            "Calculate relationship profitability, not just per-load margins—15 loads monthly at 8% might generate more total income than 3 loads monthly at 20%",
            "Reduce service quality to match the lower margins",
            "Focus only on the percentage margin since that's the key metric"
        ],
        "correct_index": 1,
        "explanation": "Don't make decisions based purely on individual load margins. Calculate relationship profitability, not just transaction profitability. A high-volume customer paying slightly lower margins might be more valuable than a customer paying high margins on infrequent shipments. Consider total income, relationship stability, and growth potential when evaluating customer relationships."
    },
    {
        "id": "q3_6_1",
        "question": "You've found a new carrier offering very competitive rates on a lane you frequently use. They have an active DOT number but you're having trouble verifying their insurance information. What should you do?",
        "choices": [
            "Use them for one test load to see how they perform, then verify insurance if they do well",
            "Do not tender freight to this carrier until you've verified they have valid commercial auto liability insurance at required levels—this is a legal requirement",
            "Ask the carrier to email you their insurance information and accept whatever they send",
            "Assume their insurance is valid since they have an active DOT number"
        ],
        "correct_index": 1,
        "explanation": "Federal regulations require brokers to verify that carriers have proper authority, insurance, and acceptable safety ratings before tendering freight. This isn't optional—it's a legal requirement that protects you from enormous liability. Using a carrier without verified proper insurance exposes you to serious financial and legal risk if accidents or cargo loss occurs."
    },
    {
        "id": "q3_6_2",
        "question": "It's Friday afternoon and you're completing paperwork for the week. You realize you haven't filed the proof of delivery for a shipment that delivered on Monday. When should you handle this?",
        "choices": [
            "It can wait until next week since it's already Friday afternoon",
            "File it immediately—organize documentation while details are fresh, and you may need these records for invoicing, disputes, or compliance purposes",
            "Only file important documents; routine PODs don't need to be saved",
            "Email it to someone else in your office to file for you"
        ],
        "correct_index": 1,
        "explanation": "Maintain organized records of all transactions and documents. Handle documentation while details are fresh, and ensure you can quickly locate any document related to any shipment. Three months later, when a customer questions a charge or you need to prove delivery, you must have immediate access to supporting documentation. Delayed or incomplete record keeping creates problems."
    },
    {
        "id": "q3_7_1",
        "question": "You notice that several carriers have mentioned capacity is getting tighter on your primary lanes over the past two weeks. What should you do with this information?",
        "choices": [
            "Keep it to yourself so competitors don't benefit from your intelligence",
            "Share this market intelligence proactively with your customers, helping them understand they may need to plan further ahead and expect slightly higher rates",
            "Wait until customers complain about rates before mentioning market conditions",
            "Immediately raise all your rates by 20%"
        ],
        "correct_index": 1,
        "explanation": "Market intelligence from carrier communication provides valuable insights. Sharing this intelligence proactively with customers demonstrates expertise and helps them make better decisions. This positions you as a trusted advisor providing value beyond just booking loads. Customers appreciate advance warning about market changes that might affect their operations."
    },
    {
        "id": "q3_7_2",
        "question": "You've been working as a freight agent for six months and notice you struggle with negotiating carrier rates effectively. How should you address this skill gap?",
        "choices": [
            "Avoid negotiating by always accepting carriers' first quoted rates",
            "Just keep doing what you're doing—you'll improve naturally over time",
            "Identify this as a skill needing development: read books on negotiation tactics, practice with lower-stakes loads, seek advice from experienced agents, and analyze what approaches work best",
            "Delegate all carrier negotiations to someone else at your brokerage"
        ],
        "correct_index": 2,
        "explanation": "Successful agents identify skills they need to improve and actively work on developing them. Continuous learning means recognizing weaknesses, studying techniques, practicing deliberately, and refining your approach based on results. Skill development requires intentional effort, not just hoping you'll improve over time."
    },
    {
        "id": "q3_8_1",
        "question": "It's 10:30 AM on a Tuesday. You have three active shipments tracking on time, no immediate issues, and your scheduled prospecting block starts at 11:00 AM. What should you do in the next 30 minutes?",
        "choices": [
            "Take a break since you're ahead of schedule",
            "Start prospecting calls 30 minutes early since active shipments are running smoothly",
            "Process administrative tasks like invoicing completed deliveries, updating documentation, or checking on upcoming shipment details",
            "Leave the office early since everything is under control"
        ],
        "correct_index": 2,
        "explanation": "When active shipments are running smoothly, use available time productively for administrative tasks or early prospecting. Batching administrative work—doing all invoicing at once, processing documentation together—improves efficiency. Don't waste productive time when you could be invoicing completed deliveries, organizing records, or handling other essential administrative tasks."
    },
    {
        "id": "q3_8_2",
        "question": "You're following up on a quote you provided yesterday when a current customer calls with an urgent issue about a delivery scheduled for today. How should you prioritize these two activities?",
        "choices": [
            "Finish the follow-up call since you already started it",
            "Immediately shift to the customer's urgent issue—active shipments always take priority over sales activities",
            "Ask the customer to hold while you finish the other call",
            "Split your attention between both calls simultaneously"
        ],
        "correct_index": 1,
        "explanation": "Active shipments and customer service always take priority. When a customer calls with an urgent issue, drop everything else and handle it immediately. You can make prospecting or follow-up calls later, but you can't recover from service failures. This prioritization builds trust and ensures operational excellence."
    },
    {
        "id": "q3_9_1",
        "question": "A driver got lost and delivered three hours late due to their GPS malfunction. The customer is upset and questioning whether they should continue using your services. How should you respond?",
        "choices": [
            "Explain it's the driver's fault, not yours, so the customer shouldn't hold it against you",
            "Blame the carrier company for giving you a bad driver",
            "Take complete ownership: 'I understand this was unacceptable. This is my load and my responsibility to fix. Here's what I'm doing to ensure it doesn't happen again, and here's how I'll make this right.'",
            "Suggest the customer should have provided better directions"
        ],
        "correct_index": 2,
        "explanation": "Take complete ownership of every shipment you book. When you accept a load, it becomes your load and you're accountable for its success regardless of what goes wrong or whose fault it might be. Customers don't care whose fault problems are—they care about results. Taking ownership builds reputation as someone who makes things happen rather than makes excuses."
    },
    {
        "id": "q3_9_2",
        "question": "A customer needs a shipment covered during extremely tight capacity. You'll need to pay carrier rates that leave you with a $50 margin instead of your typical $300 margin. The customer represents $15,000 in annual revenue. What's the best approach?",
        "choices": [
            "Decline the shipment since the margin doesn't meet your standards",
            "Tell the customer you can't help them during tight capacity periods",
            "Accept the smaller margin to preserve a valuable long-term relationship worth thousands in future revenue",
            "Lie about carrier rates being even higher so you can maintain your usual margin"
        ],
        "correct_index": 2,
        "explanation": "Prioritize long-term relationships over short-term profits. Sometimes earning a small margin (or even breaking even) maintains relationships worth thousands in future revenue. Long-term thinking focuses on building a business that generates substantial income for years, not just maximizing this quarter's commission. Customers remember agents who came through when capacity was tight."
    },
    {
        "id": "q3_9_3",
        "question": "You notice you've had three shipments this month where detention charges were disputed by customers. They all involved confusion about free time policies. What should you do?",
        "choices": [
            "Nothing—disputes are just part of the business",
            "Stop charging detention since it causes disputes",
            "Learn from the pattern: modify your process to communicate free time policies clearly upfront in rate confirmations and customer communications to prevent future disputes",
            "Blame customers for not understanding standard industry practices"
        ],
        "correct_index": 2,
        "explanation": "Continuous improvement means regularly reflecting on your performance and looking for ways to improve. When you notice patterns of disputes, identify the root cause and modify your processes to prevent future occurrences. Many disputes arise from preventable miscommunications. Learning from problems and adjusting your approach prevents repeating mistakes."
    }
]

# Chapter 4 Quizzes
chapter4_quizzes = [
    {
        "id": "q4_1_1",
        "question": "Why is equipment knowledge essential for freight agents beyond just booking loads?",
        "choices": [
            "It's only necessary to impress customers with technical jargon",
            "Accurate equipment selection prevents wasted time, damaged relationships, and costly mistakes when carriers arrive unprepared or with wrong equipment",
            "Most carriers will figure out the right equipment anyway, so detailed knowledge isn't critical",
            "Equipment knowledge is only important for flatbed specialists"
        ],
        "correct_index": 1,
        "explanation": "Equipment knowledge separates professional agents from amateurs. Incorrect equipment selection causes serious problems: carriers arriving unable to load freight, wasted time for everyone, damaged relationships with customers and carriers, and potential safety issues. You must understand what each trailer type can handle to quote loads accurately and communicate credibly."
    },
    {
        "id": "q4_2_1",
        "question": "You're quoting a load of 26 pallets of furniture. Each pallet is 48\"×40\"×72\" tall and weighs 400 pounds (total 10,400 lbs). The pallets will consume approximately 4,200 cubic feet. How many trailers do you need?",
        "choices": [
            "One trailer—the weight is only 10,400 lbs, well under the 45,000 lb capacity",
            "Two trailers—this load will cube out despite being nowhere near weight limits",
            "One trailer if you stack the pallets differently",
            "Three trailers to ensure safe transport"
        ],
        "correct_index": 1,
        "explanation": "This load cubes out. A standard dry van has approximately 4,000 cubic feet of capacity. These 26 pallets consume 4,200 cubic feet, exceeding the available space. Even though the 10,400-pound weight is far below the 45,000-pound capacity, you've filled all physical space. You need two trailers. Understanding cubing out vs. weighing out is critical for accurate quoting."
    },
    {
        "id": "q4_2_2",
        "question": "A customer requests dry van service for pickup at a small warehouse without a loading dock or forklift. What's the appropriate response?",
        "choices": [
            "Book a standard dry van—the driver will figure out loading somehow",
            "Refuse the shipment since dry vans can't accommodate this situation",
            "Quote dry van WITH liftgate service and include the additional cost, confirming the shipper can load pallets onto the liftgate platform",
            "Recommend the customer build a loading dock before shipping"
        ],
        "correct_index": 2,
        "explanation": "Dry vans load at dock height (48-52 inches off ground). Without a dock or forklift capable of reaching that height, you need liftgate service—a hydraulic platform that raises/lowers freight. This is an additional cost you must include in your pricing. Always confirm loading capabilities before finalizing equipment selection."
    },
    {
        "id": "q4_3_1",
        "question": "A pharmaceutical customer needs to ship temperature-sensitive products and says 'keep it cold.' What's your next step?",
        "choices": [
            "Book a reefer set to 35°F—that's cold enough for most products",
            "Ask for the exact temperature requirement in degrees Fahrenheit—'cold' isn't sufficient instruction for carrier operations",
            "Book a standard dry van—it will stay cold enough during transport",
            "Tell the carrier to use their best judgment on temperature"
        ],
        "correct_index": 1,
        "explanation": "Always confirm exact temperature requirements. Pharmaceuticals typically require 36°F to 46°F (2°C to 8°C), but some require more precise control. Different products have different temperature needs: frozen foods need 0°F to -10°F, fresh meat needs 28-32°F, dairy needs 34-38°F. Carriers need specific set-point temperatures, not vague instructions like 'keep it cold.'"
    },
    {
        "id": "q4_3_2",
        "question": "A carrier is picking up a refrigerated load at 2 PM. The required temperature is 38°F. When should the trailer be pre-cooled?",
        "choices": [
            "Pre-cooling isn't necessary—just turn on the unit when loading begins",
            "BEFORE loading begins—the trailer must be pre-cooled to 38°F before freight arrives. Refrigeration units maintain temperature but don't rapidly cool warm freight",
            "After loading—run the unit at maximum to bring everything down to temperature",
            "Pre-cooling only matters for frozen products, not refrigerated"
        ],
        "correct_index": 1,
        "explanation": "Pre-cooling is critical. Refrigeration units maintain temperature; they don't rapidly cool warm freight. Loading warm freight into a warm trailer can take many hours to reach proper temperature—potentially compromising product quality or safety. Always confirm with carriers: 'Please ensure the trailer is pre-cooled to [temperature] before arriving for loading.'"
    },
    {
        "id": "q4_4_1",
        "question": "You're quoting a load of steel beams that are 50 feet long, 4 feet wide, 3 feet tall, and weigh 28,000 pounds. The customer asks about weather protection. What equipment do you quote?",
        "choices": [
            "53-foot dry van with liftgate",
            "53-foot flatbed—steel is weatherproof and doesn't require tarps. Confirm securing requirements (likely chains and binders)",
            "48-foot dry van—it will fit if loaded diagonally",
            "53-foot reefer to prevent rust"
        ],
        "correct_index": 1,
        "explanation": "Steel products usually ship uncovered on flatbeds because they're weatherproof. A 50-foot beam fits on a 53-foot flatbed with room for proper securing. Tarping is unnecessary and would add cost. Steel typically secures with chains and binders. Always confirm securing requirements when booking flatbed loads."
    },
    {
        "id": "q4_4_2",
        "question": "A customer shipping palletized lumber asks if tarping is required. The carrier says tarping will add $100 to the rate. What's your recommendation?",
        "choices": [
            "Skip the tarp to save money—lumber can handle some moisture",
            "Tarp is required—moisture causes serious problems with lumber. Include the $100 charge and explain why protection is necessary",
            "Only tarp if it's raining",
            "Ask the carrier to absorb the tarping cost"
        ],
        "correct_index": 1,
        "explanation": "Lumber almost always requires tarps because moisture causes serious problems (warping, mold, structural damage). Tarping is labor-intensive (30-60+ minutes) and carries additional charges ($50-150). Always include tarping costs when required and explain the necessity to customers. This is protecting their investment, not an optional add-on."
    },
    {
        "id": "q4_5_1",
        "question": "You need to ship a piece of construction equipment that is 10.5 feet tall. On a standard flatbed (5-foot deck height), the total height would be 15.5 feet—exceeding the 13.5-14 foot legal limit. What equipment should you quote?",
        "choices": [
            "Standard flatbed—the driver can get oversize permits",
            "Step deck (drop deck) trailer with 3.5-foot well deck, allowing the 10.5-foot freight to stay under the height limit",
            "Dry van since the equipment needs protection anyway",
            "Cancel the shipment—it can't transport legally"
        ],
        "correct_index": 1,
        "explanation": "Step deck trailers have a lower well deck (approximately 3.5 feet off ground) that allows taller freight to remain under the 13.5-14 foot height limit. With a 3.5-foot deck, 10.5-foot freight totals 14 feet—legal height. Standard flatbeds with 5-foot decks can only carry 8.5-9 foot tall loads while staying legal. Step decks command premium rates but solve this exact problem."
    },
    {
        "id": "q4_6_1",
        "question": "A large manufacturer with 100 trailers wants to hire your carrier contacts to provide 'power only' service. What does this mean?",
        "choices": [
            "Carriers provide only electrical power to refrigeration units",
            "Carriers provide only the tractor (power unit) and driver—the customer provides the trailers. This allows drop-and-hook efficiency",
            "Carriers guarantee powerful engines for heavy loads",
            "This is a specialized electrical equipment transport"
        ],
        "correct_index": 1,
        "explanation": "Power only means carriers provide only the tractor and driver; the customer provides the trailer. This is common with large shippers who own trailer fleets. Carriers arrive, drop an empty trailer, hook a pre-loaded trailer, and depart quickly—eliminating wait time during loading. Rates are lower than full equipment rates but margins can be attractive because you're only sourcing tractor capacity."
    },
    {
        "id": "q4_7_1",
        "question": "A customer wants to ship a tanker load of food-grade vegetable oil. After delivery, the carrier says they want to haul a load of industrial lubricant next. Why is this problematic?",
        "choices": [
            "It's not problematic—tankers can haul any liquid",
            "Food-grade tankers cannot haul non-food products without extensive cleaning protocols. Cross-contamination risks make this unacceptable without proper procedures",
            "Vegetable oil and lubricant are similar enough that it doesn't matter",
            "This only matters if the same customer uses the tanker again"
        ],
        "correct_index": 1,
        "explanation": "Food-grade tankers must be thoroughly cleaned between loads and cannot haul non-food products without extensive cleaning protocols. Cross-contamination of food products with industrial chemicals creates serious safety and regulatory issues. This is why food-grade tanker freight is highly specialized and commands premium rates."
    },
    {
        "id": "q4_8_1",
        "question": "A customer asks about 'GVWR' when discussing equipment requirements. What does this mean?",
        "choices": [
            "Gross Vehicle Weight Rating—the maximum total weight of the vehicle including the vehicle itself plus all cargo",
            "General Vehicle Width Requirement",
            "Guaranteed Vehicle Weight Range",
            "Ground Vehicle Weight Restriction"
        ],
        "correct_index": 0,
        "explanation": "GVWR (Gross Vehicle Weight Rating) is the maximum total weight of the vehicle including the vehicle itself plus all cargo. It's the key metric determining truck classification. Understanding GVWR helps you communicate knowledgeably with carriers about appropriate equipment for different weight requirements."
    },
    {
        "id": "q4_9_1",
        "question": "A carrier mentions they need to distribute a 44,000-pound load carefully to avoid exceeding axle weight limits. Why does weight distribution matter when total weight is legal?",
        "choices": [
            "Weight distribution doesn't matter as long as total weight is under 80,000 lbs",
            "It's just a carrier preference with no legal significance",
            "Federal and state laws regulate not just total weight but how weight distributes across axles. Improper distribution can cause violations even if total weight is legal",
            "This only matters for oversized loads"
        ],
        "correct_index": 2,
        "explanation": "Federal and state regulations limit weight per axle, not just total vehicle weight. The typical 80,000-pound limit has specific sub-limits: steering axle (12,000 lbs), drive axles (34,000 lbs), trailer axles (34,000 lbs). Improper distribution can exceed individual axle limits even when total weight is legal. This is why proper loading and weight positioning matter."
    },
    {
        "id": "q4_10_1",
        "question": "You're evaluating equipment for a shipment. The freight is 44,000 lbs of temperature-sensitive pharmaceuticals that must maintain 40°F. What equipment do you select?",
        "choices": [
            "Dry van—it will stay cool enough during transport",
            "Reefer set to 40°F—temperature-sensitive pharmaceuticals require active refrigeration to maintain precise temperatures",
            "Flatbed with tarps for weather protection",
            "Standard dry van with extra insulation"
        ],
        "correct_index": 1,
        "explanation": "Temperature-sensitive freight requiring specific temperature maintenance needs a reefer. Pharmaceuticals typically require 36-46°F with precise control. Dry vans don't provide active temperature control and can't maintain specific temperatures. The systematic equipment selection process puts temperature control as Step 3: if yes, you need a reefer with the exact temperature specified."
    },
    {
        "id": "q4_10_2",
        "question": "Which of these represents the CORRECT equipment selection priority order?",
        "choices": [
            "Price first, then dimensions, then weight",
            "Physical dimensions → weight capacity → temperature control → loading method → weather protection → special regulations → customer preferences → economic efficiency",
            "Customer preferences first, then figure out what equipment works",
            "Just ask the carrier what they recommend"
        ],
        "correct_index": 1,
        "explanation": "Following a systematic evaluation process prevents equipment selection errors. The correct order is: (1) Physical dimensions—does it fit? (2) Weight capacity—can the equipment handle it? (3) Temperature control—does it need climate control? (4) Loading/unloading method—how will it load? (5) Weather protection—does it need coverage? (6) Special regulations—any regulatory requirements? (7) Customer preferences—specific requirements? (8) Economic efficiency—appropriate without being unnecessarily expensive?"
    },
    {
        "id": "q4_11_1",
        "question": "When booking a reefer load, what information is MOST critical to communicate to the carrier upfront?",
        "choices": [
            "Your commission rate and how much you're charging the customer",
            "Exact temperature requirement (e.g., '38 degrees F'), pre-cooling requirement, weight, dimensions, and food-grade requirements if applicable",
            "Just the pickup and delivery locations—carriers know how to handle reefers",
            "The weather forecast for the route"
        ],
        "correct_index": 1,
        "explanation": "When booking reefer loads, essential information includes: equipment type with exact temperature ('53-foot reefer set to 38 degrees'), weight and dimensions, special requirements ('food-grade trailer required, no previous chemical loads'), and specific instructions ('pre-cool to 38 degrees before loading'). Complete information upfront saves time and prevents carriers from arriving unprepared. Never assume carriers will 'figure it out.'"
    },
    {
        "id": "q4_11_2",
        "question": "A carrier asks for details about a flatbed load. You provide: '53-foot flatbed, 32,000 lbs.' The carrier says this isn't enough information. What critical details did you omit?",
        "choices": [
            "Nothing—weight and equipment type are sufficient",
            "Dimensions of the freight, number of pieces, whether tarping is required, securing requirements (chains/straps), and loading/unloading equipment available",
            "Only the pickup and delivery cities",
            "Your company name"
        ],
        "correct_index": 1,
        "explanation": "For flatbed loads, carriers need: dimensions and piece count ('3 pieces, largest is 24 feet long × 8 feet wide × 6 feet tall'), tarping requirements ('with tarps' or 'uncovered—steel freight'), securing requirements ('straps and edge protectors needed'), and loading/unloading details ('crane available for loading'). Flatbed freight is more variable than dry van freight, requiring more detailed communication."
    }
]

# ============================================================================
# CHAPTER 5 QUIZZES
# ============================================================================

# Quiz questions for Module 5.1
MODULE_5_1_QUIZ = [
    {
        "id": "q5_1_1",
        "question": "Why is understanding different load types and cargo categories important for a freight agent?",
        "choices": [
            "It's not important—all freight is basically the same",
            "It helps you communicate effectively with customers, select appropriate equipment, and anticipate challenges before they arise",
            "Only to sound knowledgeable in conversations",
            "It's only needed for specialized freight brokers"
        ],
        "correct_index": 1,
        "explanation": "Understanding load types helps you ask intelligent questions, provide accurate quotes, select the right equipment, and avoid costly mistakes. Every commodity has unique characteristics affecting density, fragility, value, regulatory requirements, and handling needs."
    }
]

# Quiz questions for Module 5.2
MODULE_5_2_QUIZ = [
    {
        "id": "q5_2_1",
        "question": "A customer has 24 pallets of automotive parts weighing 2,000 pounds per pallet (48,000 lbs total). What issue will you encounter when booking this load in a standard 53-foot dry van?",
        "choices": [
            "The load exceeds the trailer's 45,000-pound capacity and you'll need to remove pallets or find specialized equipment",
            "The pallets won't fit because dry vans can only hold 20 pallets",
            "Automotive parts require refrigeration",
            "No issue—this load fits perfectly"
        ],
        "correct_index": 0,
        "explanation": "Dense freight like automotive parts weighs out trailers quickly. At 2,000 lbs per pallet, 24 pallets totals 48,000 lbs, exceeding the standard 45,000-pound capacity. You'd need to reduce to 22-23 pallets or find equipment with higher capacity. Understanding whether freight will weigh out or cube out is critical for accurate quoting."
    },
    {
        "id": "q5_2_2",
        "question": "A customer says their freight 'can probably stack.' What should you do?",
        "choices": [
            "Tell the carrier the freight is stackable",
            "Assume it can't stack to be safe",
            "Don't assume—confirm with the customer whether the freight can definitely be stacked and how high it can safely stack",
            "Stack it anyway since most freight is stackable"
        ],
        "correct_index": 2,
        "explanation": "Never assume freight can be stacked without definite confirmation. 'Probably' isn't good enough. If freight cannot stack and you told the carrier it could, you create problems at pickup. Always ask: 'Can this freight be stacked? If yes, how high?' Get clear answers before dispatching."
    }
]

# Quiz questions for Module 5.3
MODULE_5_3_QUIZ = [
    {
        "id": "q5_3_1",
        "question": "A customer needs to ship tomatoes and asks what temperature you recommend. What is the correct answer?",
        "choices": [
            "0°F—frozen like most produce",
            "32-34°F—cold like lettuce and leafy greens",
            "34-38°F—dairy temperature is safe for all food",
            "50-60°F—tomatoes require warm temperatures; below 50°F causes chilling injury and flavor loss"
        ],
        "correct_index": 3,
        "explanation": "Tomatoes require 50-60°F. Temperatures below 50°F cause chilling injury and flavor loss. This is a common mistake inexperienced agents make—assuming all produce needs cold temperatures. Different fruits and vegetables have vastly different temperature requirements. Always verify specific requirements for each product."
    },
    {
        "id": "q5_3_2",
        "question": "A customer asks for a 'food-grade trailer' for canned goods. What does this typically mean?",
        "choices": [
            "A refrigerated trailer set to specific temperature",
            "A trailer that is clean, odor-free, and hasn't hauled non-food products or has been thoroughly cleaned according to food safety standards",
            "Any dry van that has been swept out",
            "A trailer certified by the FDA"
        ],
        "correct_index": 1,
        "explanation": "Food-grade trailers are those that haven't hauled non-food products (like chemicals or automotive parts) or have been thoroughly cleaned according to food safety standards. Requirements vary by customer—some accept any clean trailer, others require trailers that have only hauled food products. Always ask: 'Do you require food-grade trailers? Are there specific previous load restrictions?'"
    }
]

# Quiz questions for Module 5.4
MODULE_5_4_QUIZ = [
    {
        "id": "q5_4_1",
        "question": "Why do steel coils require special mention and extra caution when selecting carriers?",
        "choices": [
            "They're expensive and require extra insurance",
            "An improperly secured 40,000-pound coil can shift or roll, crushing the driver's cab or causing the truck to overturn—only use carriers with documented steel coil experience",
            "They require refrigeration",
            "They're not actually dangerous; the concern is overblown"
        ],
        "correct_index": 1,
        "explanation": "Steel coils are extremely heavy and dangerous if not secured properly. An improperly secured 40,000-pound coil that shifts or rolls can crush the driver's cab or cause the truck to overturn. Many carriers won't haul coils without extensive experience. Only use carriers with documented steel coil experience and proper securing equipment."
    },
    {
        "id": "q5_4_2",
        "question": "A customer needs drywall delivered and says tarping 'probably isn't necessary.' What should you tell them?",
        "choices": [
            "Agree—drywall is durable and doesn't need protection",
            "Tarping is absolutely required—even brief rain exposure can ruin entire loads worth thousands of dollars because drywall is extremely moisture-sensitive",
            "Leave it up to the carrier to decide",
            "Only tarp if heavy rain is forecasted"
        ],
        "correct_index": 1,
        "explanation": "Tarping is critical for drywall—even brief rain exposure can ruin entire loads worth thousands of dollars. Drywall is extremely fragile and moisture-sensitive. Moisture destroys it completely. Never transport drywall without tarping, regardless of weather forecasts."
    }
]

# Quiz questions for Module 5.5
MODULE_5_5_QUIZ = [
    {
        "id": "q5_5_1",
        "question": "A customer says they have a 'small CNC machine' to ship. What critical mistake would it be to assume this means it's lightweight?",
        "choices": [
            "There is no mistake—small machines are always light",
            "Small machinery can still be extremely heavy; a compact CNC machine might weigh 8,000+ pounds—always confirm exact dimensions and weights",
            "CNC machines are always shipped by air, not truck",
            "Size and weight don't matter for machinery"
        ],
        "correct_index": 1,
        "explanation": "Never assume machinery characteristics based on description alone. A 'small' lathe might be 5,000 pounds, while a 'modest' press could be 20,000 pounds. A compact CNC machine might be 8,000 pounds. Always confirm exact dimensions and weights before quoting equipment and pricing."
    },
    {
        "id": "q5_5_2",
        "question": "A machinery shipment requires crane loading and unloading. What must you confirm before booking?",
        "choices": [
            "Nothing—the carrier will bring a crane",
            "Confirm both origin and destination have adequate cranes with capacity matching or exceeding the machinery weight",
            "Only verify that the origin has a crane",
            "Just the weight of the machine"
        ],
        "correct_index": 1,
        "explanation": "Always confirm loading and unloading methods and capabilities at both locations before booking. Arriving with heavy machinery and no way to load or unload it creates expensive problems. Crane capacity must match or exceed machinery weight at both origin and destination."
    }
]

# Quiz questions for Module 5.6
MODULE_5_6_QUIZ = [
    {
        "id": "q5_6_1",
        "question": "A customer needs to ship paint products. They say it's 'just regular paint, nothing special.' What should you know?",
        "choices": [
            "Paint is general freight and requires no special handling",
            "Paint is typically classified as Class 3 Flammable Liquids, requiring hazmat endorsement, special shipping papers, placarding, and commanding 15-30% rate premium",
            "Paint only requires special handling if it's industrial paint",
            "Paint can ship in any dry van with any driver"
        ],
        "correct_index": 1,
        "explanation": "Paint is typically classified as Class 3 Flammable Liquids (hazmat). It requires drivers with hazmat endorsements, proper shipping papers, placarding, possible routing restrictions, and higher insurance ($5M vs. $750K). Many everyday products like paint, aerosols, cleaning chemicals, and batteries are hazmat. Always ask: 'Does your freight include anything flammable, corrosive, compressed, or otherwise hazardous?'"
    },
    {
        "id": "q5_6_2",
        "question": "What is the minimum cargo insurance requirement for hazmat freight requiring placarding, compared to general freight?",
        "choices": [
            "$750,000 for both",
            "$5,000,000 for hazmat vs. $750,000 for general freight",
            "$1,000,000 for both",
            "$10,000,000 for hazmat vs. $1,000,000 for general freight"
        ],
        "correct_index": 1,
        "explanation": "Hazmat requiring placarding requires minimum $5,000,000 insurance vs. $750,000 for standard freight. This higher insurance requirement affects carrier availability and costs, contributing to the 15-30% rate premium for hazmat freight."
    }
]

# Quiz questions for Module 5.7
MODULE_5_7_QUIZ = [
    {
        "id": "q5_7_1",
        "question": "A customer needs to ship electronics worth $150,000. What security measures should you implement?",
        "choices": [
            "None—standard shipping is fine",
            "Team drivers, GPS tracking, secure parking only (no truck stops), route security avoiding high-crime areas, and sealed trailers",
            "Only GPS tracking is needed",
            "Just use a reputable carrier"
        ],
        "correct_index": 1,
        "explanation": "High-value cargo (typically $100K+) requires extensive security: team drivers (truck never left unattended), GPS tracking with geofencing, secure parking at approved facilities only, route security avoiding high-crime areas, and sealed trailers with numbered seals. Standard cargo insurance only covers $100K; additional insurance is required for high-value loads."
    },
    {
        "id": "q5_7_2",
        "question": "Why do team drivers cost 50-75% more than solo drivers for high-value freight?",
        "choices": [
            "It's an arbitrary markup",
            "Two qualified drivers requiring compensation, plus the value of continuous movement reducing theft opportunities and never leaving the truck unattended",
            "Only because of fuel costs",
            "Team drivers aren't actually more expensive"
        ],
        "correct_index": 1,
        "explanation": "Team drivers cost 50-75% more because you're paying two drivers, plus the enhanced security of continuous movement (truck is never left unattended, reducing theft opportunities). One driver rests while the other drives, allowing nearly continuous movement and preventing the security risks of parking overnight at truck stops."
    }
]

# Quiz questions for Module 5.8
MODULE_5_8_QUIZ = [
    {
        "id": "q5_8_1",
        "question": "A customer needs freight to travel 1,200 miles in 24 hours. What service level is required and why can't a solo driver accomplish this?",
        "choices": [
            "Solo driver can do this easily",
            "Expedited team drivers are required because solo drivers are limited to 11 hours of driving per day under HOS regulations (~500-550 miles), while teams can cover 1,000-1,200+ miles in 24 hours",
            "Air freight is the only option",
            "Just pay the solo driver extra to drive faster"
        ],
        "correct_index": 1,
        "explanation": "Solo drivers can only drive 11 hours per day under Hours of Service regulations, covering ~500-550 miles. Covering 1,200 miles in 24 hours requires team drivers who alternate driving and resting, allowing nearly continuous movement. Team drivers cost 50-75% more but can cover 1,000-1,200+ miles in 24 hours."
    },
    {
        "id": "q5_8_2",
        "question": "For expedited freight under 1,500 miles, why might team trucking be better than air freight?",
        "choices": [
            "Air freight is always faster",
            "Team trucking often costs less than air freight while delivering in comparable time, because air freight involves multiple handoffs (trucking to airport, airport handling, flight, destination airport, trucking from airport)",
            "Air freight isn't available for distances under 1,500 miles",
            "They're exactly the same"
        ],
        "correct_index": 1,
        "explanation": "For distances under 1,500 miles, expedited team trucking often costs less than air freight while delivering in comparable time. Air freight involves trucking to origin airport, airport handling, air transport, destination airport handling, and trucking from destination airport—each transfer adds time and cost. Team drivers provide door-to-door service without multiple handoffs."
    }
]

# Quiz questions for Module 5.9
MODULE_5_9_QUIZ = [
    {
        "id": "q5_9_1",
        "question": "A customer has machinery that is 10 feet wide, 14 feet tall (on flatbed), 52 feet long, and weighs 75,000 lbs. What permits are required?",
        "choices": [
            "No permits needed—these dimensions are legal",
            "Oversize permits required for width (exceeds 8.5 feet) from every state the shipment travels through",
            "Only overweight permits needed",
            "Only the destination state requires permits"
        ],
        "correct_index": 1,
        "explanation": "This load exceeds the legal width limit of 8.5 feet, requiring oversize permits. Permits must be obtained from every state the shipment travels through. Legal limits are: 8.5' wide, 13.5-14' tall, 53' long, 80,000 lbs. This load is 10' wide (oversize), so permits are required despite being within other limits."
    },
    {
        "id": "q5_9_2",
        "question": "A customer needs an oversize load delivered 'as soon as possible' and wants to book it today for pickup tomorrow. What should you tell them?",
        "choices": [
            "No problem—book it immediately",
            "Oversize loads require substantial advance planning; permits take days to weeks to obtain and process. Routine permits need 3-7 days minimum, complex permits 2-4 weeks or more",
            "Just skip the permits and deliver quickly",
            "Permits can be obtained instantly online"
        ],
        "correct_index": 1,
        "explanation": "Never accept OS/OW loads with immediate pickup requirements. Permits take time: routine permits 3-7 days minimum, complex permits 2-4 weeks or more. Route surveys (1-2 weeks), escort arrangements (days to weeks), and specialized rigging (days to weeks) all require advance planning. Customers expecting quick turnaround don't understand regulatory requirements."
    }
]

# Quiz questions for Module 5.10
MODULE_5_10_QUIZ = [
    {
        "id": "q5_10_1",
        "question": "A customer has a 3,500-pound shipment going to a residential address without a loading dock. They need liftgate and inside delivery. What service is most appropriate?",
        "choices": [
            "Full truckload",
            "LTL (less-than-truckload) with appropriate accessorial charges for liftgate and inside delivery to residential address",
            "Partial truckload",
            "Air freight"
        ],
        "correct_index": 1,
        "explanation": "LTL is appropriate for shipments under 5,000 pounds to single destinations when cost is more important than speed. However, accessorial charges add up: liftgate ($50-150), inside delivery ($75-200), and residential delivery ($75-150). A shipment quoted at $250 might cost $475 after accessorials. Always include these charges in your quote to avoid surprise billing that damages customer relationships."
    },
    {
        "id": "q5_10_2",
        "question": "What four factors determine LTL freight classification and pricing?",
        "choices": [
            "Color, weight, distance, and time of year",
            "Density, stowability, handling, and liability",
            "Size, shape, temperature, and value",
            "Origin, destination, carrier, and customer preference"
        ],
        "correct_index": 1,
        "explanation": "LTL classification (Classes 50-500) is based on four factors: Density (weight per cubic foot—denser freight has lower classes), Stowability (how easily it fits with other freight), Handling (difficulty of loading/unloading), and Liability (risk of theft, damage, or spoilage). Understanding these helps you provide better LTL quotes. Light, bulky freight has high classifications and expensive LTL rates."
    }
]

chapter5_quizzes = MODULE_5_1_QUIZ + MODULE_5_2_QUIZ + MODULE_5_3_QUIZ + MODULE_5_4_QUIZ + MODULE_5_5_QUIZ + MODULE_5_6_QUIZ + MODULE_5_7_QUIZ + MODULE_5_8_QUIZ + MODULE_5_9_QUIZ + MODULE_5_10_QUIZ

# Chapter 6 Quiz Questions
MODULE_6_1_QUIZ = [
    {
        "id": "q6_1_1",
        "scenario": "You're a new freight agent learning about the regulatory landscape. A customer asks why you need to understand regulations when carriers and drivers are responsible for compliance.",
        "question": "Why is it important for freight agents to understand freight regulations even though carriers bear primary responsibility for compliance?",
        "options": [
            "A) To become certified as a compliance officer",
            "B) To set realistic expectations, avoid legal problems, and prevent commitments that violate regulations or expose parties to liability",
            "C) To take over the driver's responsibilities",
            "D) Regulations only apply to carriers, not freight agents"
        ],
        "correct_index": 1,
        "explanation": "While drivers and carriers bear primary responsibility for compliance, understanding regulations helps you set realistic expectations, avoid legal problems, and serve customers effectively. You don't need to become a regulatory expert, but understanding the basics prevents you from making commitments that violate regulations or expose you, your customers, or your carriers to liability. This knowledge is essential for professional freight agents."
    }
]

MODULE_6_2_QUIZ = [
    {
        "id": "q6_2_1",
        "scenario": "Your customer requests a 1,200-mile shipment picked up Friday at 6 PM and delivered Monday at 8 AM with a solo driver. You need to explain why this timeline is unrealistic due to Hours of Service regulations.",
        "question": "What is the maximum realistic distance a solo driver can cover per day while complying with the 11-hour driving limit?",
        "options": [
            "A) 600-650 miles per day",
            "B) 500-550 miles per day",
            "C) 700-750 miles per day",
            "D) 400-450 miles per day"
        ],
        "correct_index": 1,
        "explanation": "A solo driver can realistically cover 500-550 miles in an 11-hour driving day when accounting for fuel stops, meal breaks, traffic, and the mandatory 30-minute break requirement. Some agents quote 600-650 miles per day, but this requires nearly perfect conditions. Conservative estimates prevent disappointed customers. For a 1,200-mile trip, plan for at least 2.5 driving days plus rest periods, meaning 3+ calendar days total."
    },
    {
        "id": "q6_2_2",
        "scenario": "A driver starts their workday at 7:00 AM with a pre-trip inspection. They spend 3 hours in detention at the shipper, then drive for 8 hours. It's now 6:00 PM.",
        "question": "How much more driving time does the driver have available before their 14-hour duty window closes?",
        "options": [
            "A) 3 hours of driving time remaining",
            "B) No more driving time—the 14-hour window closes at 9:00 PM regardless of detention",
            "C) 6 hours of driving time remaining",
            "D) Unlimited time if they take a 30-minute break"
        ],
        "correct_index": 1,
        "explanation": "The 14-hour duty window starts when ANY work-related activity begins (7:00 AM) and runs continuously for 14 hours, closing at 9:00 PM. The driver has already used 11 hours (3 hours detention + 8 hours driving), leaving only 3 hours until the window closes. However, they've used 8 of their 11-hour driving limit, so they can only drive 2 more hours. Detention time consumes the duty window without producing miles—a key reason detention affects delivery schedules and why detention charges exist."
    }
]

MODULE_6_3_QUIZ = [
    {
        "id": "q6_3_1",
        "scenario": "Your carrier quotes include 2 hours of free time at pickup and delivery. A driver spends 6 hours in detention at the shipper's dock. The carrier wants to charge detention fees.",
        "question": "What is the correct detention charge for this scenario if the carrier charges $50 per hour?",
        "options": [
            "A) $300 (6 hours × $50)",
            "B) $200 (4 hours beyond free time × $50)",
            "C) $250 (5 hours × $50)",
            "D) $100 (2 hours × $50)"
        ],
        "correct_index": 1,
        "explanation": "With 2 hours of standard free time included, detention charges apply only to the time BEYOND the free time. 6 total hours - 2 free hours = 4 billable hours. 4 hours × $50 = $200. Detention charges compensate carriers for time that consumes the driver's 14-hour duty window without producing revenue miles. Always communicate free time expectations and detention rates clearly when booking loads."
    }
]

MODULE_6_4_QUIZ = [
    {
        "id": "q6_4_1",
        "scenario": "A customer's load weighs 45,000 pounds total—well under the 80,000-pound gross vehicle weight limit. However, all freight is loaded in the front half of the trailer.",
        "question": "Why is this load potentially illegal despite being under the gross weight limit?",
        "options": [
            "A) The trailer axles may exceed the 34,000-pound tandem limit due to improper weight distribution",
            "B) Loads over 40,000 pounds always require permits regardless of distribution",
            "C) The weight is too heavy for standard dry van trailers",
            "D) Federal law requires freight to be distributed evenly across the entire trailer length"
        ],
        "correct_index": 0,
        "explanation": "Weight must distribute properly across ALL axle sets, not just stay under the 80,000-pound gross limit. Loading all freight at the trailer's front concentrates excessive weight on the trailer's front axle set, potentially exceeding the 34,000-pound trailer axle limit. The load is illegal despite being under gross weight capacity. Federal limits are: 12,000 lbs steer axle, 34,000 lbs drive axles, 34,000 lbs trailer axles. Proper weight distribution is critical—always confirm customers' weights include pallets, packaging, and all materials."
    },
    {
        "id": "q6_4_2",
        "scenario": "A customer estimates their freight weighs 42,000 pounds but you're not confident in their estimate. They forgot to mention the freight is on wooden pallets.",
        "question": "What is the best practice for managing this weight uncertainty?",
        "options": [
            "A) Quote the load at exactly 42,000 pounds since that's what the customer said",
            "B) Refuse the load due to weight uncertainty",
            "C) Build safety margins and plan for 44,000-45,000 pounds, confirming weight includes pallets",
            "D) Always subtract 10% from customer weight estimates"
        ],
        "correct_index": 2,
        "explanation": "Be conservative with weight estimates. Freight often weighs more than customers estimate because they forget to include pallet weights (40-70 pounds each), packaging materials, crates, or moisture content. ALWAYS ask: 'Does this weight include pallets, packaging, and all materials, or is it just the product weight?' Build safety margins—if a customer says 42,000 pounds and you're not confident, plan for 44,000-45,000 pounds. Better to have extra capacity than discover the load is overweight at weigh stations, which causes fines, delays, and damaged relationships."
    }
]

MODULE_6_5_QUIZ = [
    {
        "id": "q6_5_1",
        "scenario": "A customer needs to ship freight that is 11 feet wide and 15 feet tall. The shipment travels through 3 states.",
        "question": "What permitting requirements apply to this moderately oversize load?",
        "options": [
            "A) No permits needed if traveling on interstate highways",
            "B) Oversize permits required from all 3 states, route surveys may be needed, processing takes days to weeks, costs $300-800 per state",
            "C) Single federal permit covers all states, same-day processing",
            "D) Only the origin state requires a permit"
        ],
        "correct_index": 1,
        "explanation": "Freight exceeding legal dimensions (8.5' wide, 13.5-14' tall) requires oversize permits from EVERY state traveled. This 11' wide × 15' tall load is moderately oversize, requiring: permits from all 3 states, possible route surveys, days-to-weeks processing time, costs of $300-800 per state, likely travel restrictions (no nighttime/weekends/holidays), and possible escort vehicles. Lead time is critical—never accept loads requiring immediate pickup when permits haven't been obtained. The permitting process alone can take days or weeks."
    }
]

MODULE_6_6_QUIZ = [
    {
        "id": "q6_6_1",
        "scenario": "You're quoting a load of paint (Class 3 Flammable Liquid) requiring placards. The carrier must have appropriate insurance and the driver needs special qualifications.",
        "question": "What are the minimum insurance and driver requirements for placarded hazmat freight?",
        "options": [
            "A) $750,000 insurance minimum, no special driver requirements",
            "B) $1,000,000 insurance minimum, hazmat endorsement required",
            "C) $5,000,000 insurance minimum, hazmat endorsement with TSA background check required",
            "D) $2,000,000 insurance minimum, commercial driver's license required"
        ],
        "correct_index": 2,
        "explanation": "Hazmat requiring placarding needs: $5,000,000 minimum cargo liability insurance (vs. $750,000 for general freight), and drivers must have hazmat endorsements obtained through specialized written testing, TSA background check (2-4 weeks processing), fingerprinting, and renewal every few years. This higher insurance requirement and limited driver availability (not all drivers maintain hazmat endorsements) means hazmat freight commands 15-30% premium rates. Always verify complete shipping papers and proper placarding before tendering hazmat loads."
    },
    {
        "id": "q6_6_2",
        "scenario": "A hazmat shipment requires detailed shipping papers. The shipper provides generic descriptions instead of proper regulatory names.",
        "question": "What required information must hazmat shipping papers include?",
        "options": [
            "A) Only the weight and destination address",
            "B) Product name, weight, and delivery date",
            "C) Proper shipping name, hazard class, UN/NA number, packing group, quantity, number/type of packages, and emergency response phone number",
            "D) Commodity description and shipper contact information"
        ],
        "correct_index": 2,
        "explanation": "Hazmat shipping papers require: Proper shipping name (from Hazardous Materials Table, not generic descriptions), Hazard class or division (Class 1-9 with subdivisions), UN or NA identification number (four-digit number identifying the specific material), Packing group when applicable (I, II, or III indicating danger level), Quantity of hazmat, Number and type of packages, and Emergency response telephone number providing 24/7 contact. Shippers are responsible for proper classification and documentation, but verify documentation is complete before tendering hazmat loads. Incomplete paperwork creates liability for everyone involved."
    }
]

MODULE_6_7_QUIZ = [
    {
        "id": "q6_7_1",
        "scenario": "You're arranging a reefer load of dairy products. The customer mentions the trailer must be pre-cooled and temperature records maintained.",
        "question": "Which regulation governs these food transportation requirements?",
        "options": [
            "A) OSHA workplace safety regulations",
            "B) The Food Safety Modernization Act (FSMA) Sanitary Transportation Rule",
            "C) Department of Transportation (DOT) hazmat regulations",
            "D) Environmental Protection Agency (EPA) refrigerant regulations"
        ],
        "correct_index": 1,
        "explanation": "The Food Safety Modernization Act (FSMA) Sanitary Transportation Rule requires: vehicles designed and maintained to prevent contamination, pre-cooling to required temperatures before loading, monitoring and recording temperature data when required, segregation from non-food items, cleaning/sanitizing between loads when necessary to prevent allergen cross-contact, documented training for personnel, and records maintained for at least 12 months. As a freight agent, understanding these requirements helps you select appropriate carriers, communicate customer requirements clearly, and set appropriate rates reflecting the additional compliance burden."
    }
]

MODULE_6_8_QUIZ = [
    {
        "id": "q6_8_1",
        "scenario": "A driver encounters an unexpected snowstorm that wasn't forecasted when their trip began. The storm significantly slows their progress.",
        "question": "What HOS flexibility does the Adverse Driving Conditions exception provide?",
        "options": [
            "A) Unlimited driving time until the driver reaches their destination",
            "B) The driver may extend the 11-hour driving limit by up to 2 hours to reach a safe location",
            "C) The driver can skip the mandatory 10-hour rest period",
            "D) The 14-hour duty window extends to 18 hours"
        ],
        "correct_index": 1,
        "explanation": "When drivers encounter adverse driving conditions not apparent when the trip began (unexpected snowstorms, fog, accidents causing traffic), they may extend the 11-hour driving limit by up to 2 hours to reach a safe location. 'Adverse conditions' must be: unexpected at trip start (checking weather forecasts means anticipated snow doesn't qualify), creating danger or significantly slowing progress, and legitimate reasons to extend driving time. This exception provides some flexibility for genuine emergencies but cannot be planned around or used routinely. The 14-hour duty window does not extend."
    }
]

MODULE_6_9_QUIZ = [
    {
        "id": "q6_9_1",
        "scenario": "You're vetting a new carrier. A colleague suggests skipping the insurance verification step to save time since the carrier seems reputable.",
        "question": "Why is proper carrier vetting legally required and not optional?",
        "options": [
            "A) Federal law requires all carriers to be vetted every 30 days",
            "B) Courts have held brokers liable for selecting unfit, uninsured, or improperly authorized carriers—proper vetting is legal protection",
            "C) Carrier vetting is only recommended best practice, not legally required",
            "D) Vetting is only required for hazmat carriers"
        ],
        "correct_index": 1,
        "explanation": "Courts have held brokers liable for selecting carriers who are unfit, uninsured, or improperly authorized. This is why proper carrier vetting is legally required, not just good practice. To protect against negligence claims: verify every carrier's operating authority with FMCSA, confirm insurance coverage with certificates listing appropriate limits, check safety ratings and inspection histories, document all vetting activities, and only use carriers meeting your brokerage's qualification standards. If you use an unqualified carrier and problems result, you face potential liability."
    },
    {
        "id": "q6_9_2",
        "scenario": "The Carmack Amendment governs interstate freight claims. A customer's load was damaged during transportation and they want to file a claim.",
        "question": "What are the time requirements for filing freight claims under the Carmack Amendment?",
        "options": [
            "A) Claims must be filed within 30 days, lawsuits within 6 months",
            "B) Claims must be filed within 9 months, lawsuits within 2 years of claim denial",
            "C) Claims must be filed immediately, lawsuits within 1 year",
            "D) No time limits apply to freight claims"
        ],
        "correct_index": 1,
        "explanation": "The Carmack Amendment key provisions include: Carriers are liable for actual loss or damage to freight they accept for transportation (subject to certain defenses like acts of God, shipper fault, inherent vice), Claimants must file claims within specified timeframes (typically 9 months for loss/damage claims), Claims must include documentation proving loss/damage, value, and carrier responsibility, and Lawsuits must be filed within 2 years of claim denial. Understanding Carmack helps you explain claims processes to customers and understand carrier liability when problems occur."
    }
]

MODULE_6_10_QUIZ = [
    {
        "id": "q6_10_1",
        "scenario": "You're quoting a delivery to a residential address. The customer expects standard freight service pricing.",
        "question": "What challenges make residential deliveries more expensive than commercial deliveries?",
        "options": [
            "A) Residences always require specialized refrigerated equipment",
            "B) Limited maneuverability, lack of loading equipment, property damage risk, parking restrictions, and signature requirements",
            "C) Residential deliveries can only occur on weekends",
            "D) Federal regulations prohibit freight deliveries to residential addresses"
        ],
        "correct_index": 1,
        "explanation": "Residential deliveries present significant challenges: Limited maneuverability (residential streets aren't designed for 53-foot trucks—tight turns, low-hanging trees, narrow roads create navigation difficulties), Lack of loading equipment (residences lack forklifts and loading docks, requiring manual unloading that's time-consuming and increases injury risk), Property damage risk (driveways, lawns, mailboxes can be damaged by large trucks), Parking restrictions (many areas prohibit/restrict commercial vehicle parking), and Signature requirements (finding someone home to sign creates scheduling complexity). Residential deliveries typically carry $75-150 surcharges. Always confirm if delivery is residential when quoting."
    },
    {
        "id": "q6_10_2",
        "scenario": "A customer needs a liftgate for delivery because the receiving location has no loading dock. The freight weighs 4,200 pounds.",
        "question": "What is a critical consideration regarding liftgate capacity for this shipment?",
        "options": [
            "A) Liftgates can handle unlimited weight",
            "B) Standard liftgates handle 3,000-5,000 pounds—this freight is near or at capacity limits and may require verification",
            "C) Liftgates are only required for residential deliveries",
            "D) Liftgates add $500+ to freight charges"
        ],
        "correct_index": 1,
        "explanation": "Standard liftgates handle 3,000-5,000 pounds depending on equipment. This 4,200-pound freight is near or potentially at capacity limits. Heavy items may exceed liftgate capacity requiring different solutions. OSHA requires liftgates meet safety standards including load capacity ratings clearly marked, safety mechanisms preventing accidental lowering, and proper maintenance/inspection. Liftgate service typically adds $50-100 to freight charges. Always confirm delivery locations have docks or liftgates when booking loads—carriers arriving at ground-level locations without dock or liftgate service cannot complete deliveries."
    }
]

MODULE_6_11_QUIZ = [
    {
        "id": "q6_11_1",
        "scenario": "You're booking a shipment from the U.S. to Canada. The customer asks why there are delays at the border even with proper documentation.",
        "question": "What factors contribute to border crossing delays even with proper documentation?",
        "options": [
            "A) Borders close at night",
            "B) Customs inspection time (varies from quick to hours), traffic congestion, random detailed inspections, and seasonal variations",
            "C) All cross-border shipments must wait exactly 24 hours at the border",
            "D) Canadian carriers cannot enter the United States"
        ],
        "correct_index": 1,
        "explanation": "Even with proper documentation, border crossings introduce delays: Inspection time (Customs and Border Protection inspections vary from quick clearances to detailed inspections taking hours), Traffic (major border crossings experience significant congestion during peak periods), Random inspections (some trucks selected for detailed inspections regardless of documentation quality), and Seasonal variations (holiday periods see increased traffic and longer waits). Build extra time into cross-border transit estimates. A domestic 500-mile trip might take one day, but a 500-mile cross-border trip might require two days accounting for border crossing time. Carriers must have country-specific operating authority beyond U.S. domestic authority."
    }
]

chapter6_quizzes = MODULE_6_1_QUIZ + MODULE_6_2_QUIZ + MODULE_6_3_QUIZ + MODULE_6_4_QUIZ + MODULE_6_5_QUIZ + MODULE_6_6_QUIZ + MODULE_6_7_QUIZ + MODULE_6_8_QUIZ + MODULE_6_9_QUIZ + MODULE_6_10_QUIZ + MODULE_6_11_QUIZ


def parse_project_outline(markdown_text: str):
    chapters_by_id = {}
    has_glossary = False
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        m1 = re.match(r"^Chapter\s+(\d+):\s*(.+)$", line, flags=re.IGNORECASE)
        if m1:
            cid = int(m1.group(1))
            title = m1.group(2).strip()
            # Convert to title case if it's all uppercase
            if title.isupper():
                title = title.title()
            chapters_by_id[cid] = {"id": cid, "title": title}
            continue
        m2 = re.match(r"^CHAPTER\s+(\d+):\s*(.+)$", line, flags=re.IGNORECASE)
        if m2 and int(m2.group(1)) not in chapters_by_id:
            cid = int(m2.group(1))
            title = m2.group(2).strip()
            # Convert to title case if it's all uppercase
            if title.isupper():
                title = title.title()
            chapters_by_id[cid] = {"id": cid, "title": title}
        # Check for glossary
        if re.match(r"^GLOSSARY OF FREIGHT AGENT TERMS$", line, flags=re.IGNORECASE):
            has_glossary = True
    chapters = [chapters_by_id[k] for k in sorted(chapters_by_id.keys())]
    # Add glossary as a special entry after chapters
    if has_glossary:
        chapters.append({"id": "glossary", "title": "Glossary"})
    print(f"[parse_project_outline] Found {len(chapters)} chapters (including glossary: {has_glossary})")
    return chapters


def extract_chapter_content(markdown_text: str, chapter_id: int):
    # Match only uppercase CHAPTER headers (not TOC-style "Chapter")
    chapter_header_pattern = re.compile(rf"^CHAPTER\s+{chapter_id}:\s*(.+)$")
    next_chapter_header_pattern = re.compile(r"^CHAPTER\s+\d+:\s*")
    module_header_pattern = re.compile(r"^Module\s+(\d+\.\d+):\s*(.+)$")
    summary_header_pattern = re.compile(rf"^CHAPTER\s+{chapter_id}\s+SUMMARY.*$", re.IGNORECASE)
    action_items_header_pattern = re.compile(rf"^ACTION\s+ITEMS\s+FOR\s+CHAPTER\s+{chapter_id}\s*$", re.IGNORECASE)

    lines = markdown_text.splitlines()
    in_chapter = False
    chapter_title = None
    intro_lines = []
    modules = []
    current_module = None
    summary_lines = []
    in_summary = False
    action_items_lines = []
    in_action_items = False

    for raw_line in lines:
        stripped = raw_line.strip()
        enter = chapter_header_pattern.match(stripped)
        if not in_chapter and enter:
            in_chapter = True
            chapter_title = enter.group(1).strip()
            # Convert to title case if it's all uppercase
            if chapter_title.isupper():
                chapter_title = chapter_title.title()
            continue
        if not in_chapter:
            continue
        if next_chapter_header_pattern.match(stripped):
            break
        if summary_header_pattern.match(stripped):
            in_summary = True
            in_action_items = False
            if current_module:
                modules.append(current_module)
                current_module = None
            continue
        if action_items_header_pattern.match(stripped):
            in_action_items = True
            in_summary = False
            if current_module:
                modules.append(current_module)
                current_module = None
            continue
        m = module_header_pattern.match(stripped)
        if m and not in_summary and not in_action_items:
            if current_module:
                modules.append(current_module)
            current_module = {"id": m.group(1), "title": m.group(2).strip(), "content": []}
            continue
        if in_summary:
            summary_lines.append(raw_line)
        elif in_action_items:
            action_items_lines.append(raw_line)
        elif current_module is not None:
            current_module["content"].append(raw_line)
        else:
            if stripped != "":
                intro_lines.append(raw_line)
    if current_module:
        modules.append(current_module)

    print(
        f"[extract_chapter_content] ch={chapter_id} modules={len(modules)} "
        f"summary={'yes' if summary_lines else 'no'} action_items={'yes' if action_items_lines else 'no'}"
    )

    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter_title or "",
        "intro": "\n".join(intro_lines).strip() if intro_lines else None,
        "modules": modules,
        "summary": "\n".join(summary_lines).strip() if summary_lines else None,
        "action_items": "\n".join(action_items_lines).strip() if action_items_lines else None,
    }


def preprocess_content(text: str) -> str:
    """Add markdown formatting to plain text content by detecting patterns."""
    if not text:
        return ""
    
    lines = text.split('\n')
    processed = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            processed.append('')
            continue
        
        # Detect section headers - short lines (< 50 chars) followed by content
        # Common patterns: "Time Savings", "Risk Management", "Months 1-3: The Learning Phase"
        is_section_header = False
        if len(stripped) < 70 and i < len(lines) - 1:
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            # If this line is short and next line is substantial content (not another header)
            if next_line and len(next_line) > 50:
                # Check if it looks like a header (title case, ends with colon, or short phrase)
                if (stripped[0].isupper() and 
                    (stripped.endswith(':') or 
                     stripped.count(' ') <= 5 or
                     any(stripped.startswith(prefix) for prefix in ['Months ', 'Year ', 'Why ', 'What ', 'The ']))):
                    is_section_header = True
        
        if is_section_header:
            # Add blank line before header for spacing and make it bold
            if processed and processed[-1] != '':
                processed.append('')
            processed.append(f"**{stripped}**")
            processed.append('')
        else:
            processed.append(line)
    
    return '\n'.join(processed)


def process_callouts(text: str) -> str:
    """Convert callout syntax [TYPE] content to HTML with special styling."""
    if not text:
        return ""
    
    # Pattern: [TYPE] Content (on its own line or paragraph)
    callout_pattern = re.compile(r'\[([A-Z\s]+)\]\s*(.+?)(?=\n\n|\[(?:[A-Z\s]+)\]|$)', re.DOTALL)
    
    def replace_callout(match):
        callout_type = match.group(1).strip()
        content = match.group(2).strip()
        
        # Map types to styles and icons
        styles = {
            'PRO TIP': ('callout-tip', '💡'),
            'COMMON MISTAKE': ('callout-warning', '⚠️'),
            'REAL EXAMPLE': ('callout-example', '📊'),
            'KEY TAKEAWAY': ('callout-key', '🎯'),
            'IMPORTANT': ('callout-important', '⚡'),
            'NOTE': ('callout-note', '📝')
        }
        
        css_class, icon = styles.get(callout_type, ('callout-default', '📌'))
        
        return f'<div class="callout {css_class}"><div class="callout-title">{icon} <strong>{callout_type}</strong></div><div class="callout-content">{content}</div></div>\n\n'
    
    return callout_pattern.sub(replace_callout, text)


def convert_to_html(text: str) -> str:
    """Convert markdown text to HTML, preserving formatting."""
    if not text:
        return ""
    
    # Process callouts first (before markdown conversion)
    text_with_callouts = process_callouts(text)
    
    # Preprocess to add markdown formatting
    formatted_text = preprocess_content(text_with_callouts)
    
    # Convert markdown to HTML with extensions for better formatting
    md = markdown.Markdown(extensions=['nl2br', 'sane_lists'])
    return md.convert(formatted_text)


def estimate_visual_height(line: str, is_in_callout: bool = False, is_callout_start: bool = False) -> float:
    """
    Estimate the visual height cost of a line of text.
    Returns a "height score" where 1.0 = one line of regular text.
    
    Callouts are much taller due to borders, padding, and styling.
    """
    stripped = line.strip()
    
    # Empty lines
    if not stripped:
        return 0.5 if not is_in_callout else 0.3
    
    # Callout start line - includes title bar with icon + padding
    if is_callout_start:
        return 4.0  # Title + top padding + borders
    
    # Content inside callout - extra padding and line spacing
    if is_in_callout:
        char_count = len(stripped)
        # Callouts have padding and styled boxes, so they're taller
        lines_of_text = max(1, char_count / 50)  # ~50 chars per line in callouts
        return lines_of_text * 1.8  # 1.8x taller due to padding
    
    # Bold headers
    if stripped.startswith('**') and stripped.endswith('**'):
        return 2.5  # Headers are larger and have spacing
    
    # Regular text - estimate lines based on character count
    char_count = len(stripped)
    if char_count == 0:
        return 0.5
    
    # Assume ~60 chars per line for regular text
    lines_of_text = max(1, char_count / 60)
    return lines_of_text * 1.2  # Account for line height


def split_content_into_pages(content_text: str, max_height_score: float = 27.5) -> list:
    """
    Split long content into multiple pages based on estimated VISUAL HEIGHT.
    
    Instead of counting characters, we estimate how tall content will render:
    - Regular text: ~1.0-1.2 height units per line
    - Bold headers: ~2.5 height units (larger font + spacing)
    - Callout boxes: ~4.0 for title + 1.8x per line of content (padding + borders)
    
    Max height score of 28.0 = approximately viewport height without scrolling.
    Never splits callout blocks ([TYPE] content).
    """
    if not content_text:
        return [content_text]
    
    # Split by lines first
    lines = content_text.split('\n')
    pages = []
    current_page = []
    current_height = 0.0
    in_callout = False
    callout_lines = []
    callout_pattern = re.compile(r'^\[([A-Z\s]+)\]')
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect callout start
        is_callout_start = callout_pattern.match(stripped) is not None
        if is_callout_start:
            in_callout = True
            callout_lines = [line]
            continue  # Don't add yet, collect whole callout first
        
        # If in callout, collect lines
        if in_callout:
            callout_lines.append(line)
            # Detect callout end (empty line after content OR next line is not indented/content)
            is_last_line = (i == len(lines) - 1)
            if (stripped == '' and len(callout_lines) > 1) or is_last_line:
                # Callout is complete, calculate its total height
                callout_height = estimate_visual_height(callout_lines[0], False, True)  # Title
                for callout_line in callout_lines[1:]:
                    callout_height += estimate_visual_height(callout_line, True, False)
                
                # Be conservative - use 85% threshold for callouts to ensure they fit
                safety_threshold = max_height_score * 0.85
                
                # If adding callout would exceed safe limit, start new page
                if current_height + callout_height > safety_threshold and current_page:
                    pages.append('\n'.join(current_page))
                    current_page = callout_lines.copy()
                    current_height = callout_height
                else:
                    current_page.extend(callout_lines)
                    current_height += callout_height
                
                in_callout = False
                callout_lines = []
            continue
        
        # Regular line (not in callout)
        line_height = estimate_visual_height(line, False, False)
        
        # If adding this line would exceed limit, start new page
        if current_height + line_height > max_height_score and current_page:
            # If current line is a header, include it in next page
            if stripped.startswith('**'):
                pages.append('\n'.join(current_page))
                current_page = [line]
                current_height = line_height
            else:
                current_page.append(line)
                pages.append('\n'.join(current_page))
                current_page = []
                current_height = 0.0
        else:
            current_page.append(line)
            current_height += line_height
    
    # Add any remaining callout lines if still in callout (shouldn't happen but safety)
    if callout_lines:
        current_page.extend(callout_lines)
    
    # Add the last page
    if current_page:
        pages.append('\n'.join(current_page))
    
    return pages


def extract_glossary(markdown_text: str):
    """Extract glossary terms from the markdown."""
    lines = markdown_text.splitlines()
    in_glossary = False
    glossary_lines = []
    
    for raw_line in lines:
        stripped = raw_line.strip()
        if re.match(r"^GLOSSARY OF FREIGHT AGENT TERMS$", stripped, flags=re.IGNORECASE):
            in_glossary = True
            continue
        if in_glossary and stripped:
            glossary_lines.append(raw_line)
    
    print(f"[extract_glossary] Found {len(glossary_lines)} glossary terms")
    return "\n".join(glossary_lines).strip()


def parse_glossary_terms(markdown_text: str):
    """Parse glossary into structured term objects."""
    glossary_text = extract_glossary(markdown_text)
    terms = []
    
    # Pattern: "Mod X.X - Term Name - Definition"
    pattern = re.compile(r'^(Mod\s+[\d.]+)\s*-\s*([^-]+?)\s*-\s*(.+)$')
    
    for line in glossary_text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if match:
            terms.append({
                'module': match.group(1).strip(),
                'name': match.group(2).strip(),
                'definition': match.group(3).strip()
            })
    
    print(f"[parse_glossary_terms] Parsed {len(terms)} structured terms")
    return terms


def get_module_completion_status(session_quiz_answers, module_id):
    """Check if all quizzes for a module are completed."""
    quiz_map = {
        "1.1": MODULE_1_1_QUIZ,
        "1.2": MODULE_1_2_QUIZ,
        "1.3": MODULE_1_3_QUIZ,
        "1.4": MODULE_1_4_QUIZ,
        "1.5": MODULE_1_5_QUIZ,
        "1.6": MODULE_1_6_QUIZ,
        "2.1": MODULE_2_1_QUIZ,
        "2.2": MODULE_2_2_QUIZ,
        "2.3": MODULE_2_3_QUIZ,
        "2.4": MODULE_2_4_QUIZ,
        "2.5": MODULE_2_5_QUIZ,
        "2.6": MODULE_2_6_QUIZ,
        "2.7": MODULE_2_7_QUIZ,
        "2.8": MODULE_2_8_QUIZ,
        "2.9": MODULE_2_9_QUIZ,
        "3.1": [q for q in chapter3_quizzes if q["id"].startswith("q3_1")],
        "3.2": [q for q in chapter3_quizzes if q["id"].startswith("q3_2")],
        "3.3": [q for q in chapter3_quizzes if q["id"].startswith("q3_3")],
        "3.4": [q for q in chapter3_quizzes if q["id"].startswith("q3_4")],
        "3.5": [q for q in chapter3_quizzes if q["id"].startswith("q3_5")],
        "3.6": [q for q in chapter3_quizzes if q["id"].startswith("q3_6")],
        "3.7": [q for q in chapter3_quizzes if q["id"].startswith("q3_7")],
        "3.8": [q for q in chapter3_quizzes if q["id"].startswith("q3_8")],
        "3.9": [q for q in chapter3_quizzes if q["id"].startswith("q3_9")],
        "4.1": [q for q in chapter4_quizzes if q["id"].startswith("q4_1_")],
        "4.2": [q for q in chapter4_quizzes if q["id"].startswith("q4_2_")],
        "4.3": [q for q in chapter4_quizzes if q["id"].startswith("q4_3_")],
        "4.4": [q for q in chapter4_quizzes if q["id"].startswith("q4_4_")],
        "4.5": [q for q in chapter4_quizzes if q["id"].startswith("q4_5_")],
        "4.6": [q for q in chapter4_quizzes if q["id"].startswith("q4_6_")],
        "4.7": [q for q in chapter4_quizzes if q["id"].startswith("q4_7_")],
        "4.8": [q for q in chapter4_quizzes if q["id"].startswith("q4_8_")],
        "4.9": [q for q in chapter4_quizzes if q["id"].startswith("q4_9_")],
        "4.10": [q for q in chapter4_quizzes if q["id"].startswith("q4_10_")],
        "4.11": [q for q in chapter4_quizzes if q["id"].startswith("q4_11_")],
        "5.1": [q for q in chapter5_quizzes if q["id"].startswith("q5_1_")],
        "5.2": [q for q in chapter5_quizzes if q["id"].startswith("q5_2_")],
        "5.3": [q for q in chapter5_quizzes if q["id"].startswith("q5_3_")],
        "5.4": [q for q in chapter5_quizzes if q["id"].startswith("q5_4_")],
        "5.5": [q for q in chapter5_quizzes if q["id"].startswith("q5_5_")],
        "5.6": [q for q in chapter5_quizzes if q["id"].startswith("q5_6_")],
        "5.7": [q for q in chapter5_quizzes if q["id"].startswith("q5_7_")],
        "5.8": [q for q in chapter5_quizzes if q["id"].startswith("q5_8_")],
        "5.9": [q for q in chapter5_quizzes if q["id"].startswith("q5_9_")],
        "5.10": [q for q in chapter5_quizzes if q["id"].startswith("q5_10_")],
        "6.1": [q for q in chapter6_quizzes if q["id"].startswith("q6_1_")],
        "6.2": [q for q in chapter6_quizzes if q["id"].startswith("q6_2_")],
        "6.3": [q for q in chapter6_quizzes if q["id"].startswith("q6_3_")],
        "6.4": [q for q in chapter6_quizzes if q["id"].startswith("q6_4_")],
        "6.5": [q for q in chapter6_quizzes if q["id"].startswith("q6_5_")],
        "6.6": [q for q in chapter6_quizzes if q["id"].startswith("q6_6_")],
        "6.7": [q for q in chapter6_quizzes if q["id"].startswith("q6_7_")],
        "6.8": [q for q in chapter6_quizzes if q["id"].startswith("q6_8_")],
        "6.9": [q for q in chapter6_quizzes if q["id"].startswith("q6_9_")],
        "6.10": [q for q in chapter6_quizzes if q["id"].startswith("q6_10_")],
        "6.11": [q for q in chapter6_quizzes if q["id"].startswith("q6_11_")],
    }
    
    if module_id not in quiz_map:
        return True  # Modules without quizzes are considered complete
    
    quiz_questions = quiz_map[module_id]
    for question in quiz_questions:
        if not session_quiz_answers.get(question["id"], False):
            return False
    return True


def get_chapter_completion_status(session_quiz_answers, chapter_num):
    """Check if all modules in a chapter are completed."""
    chapter_modules = {
        1: ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"],
        2: ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"],
        3: ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9"],
        4: ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9", "4.10", "4.11"],
        5: ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9", "5.10"],
        6: ["6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "6.8", "6.9", "6.10", "6.11"],
    }
    
    if chapter_num not in chapter_modules:
        return True
    
    module_ids = chapter_modules[chapter_num]
    for mod_id in module_ids:
        if not get_module_completion_status(session_quiz_answers, mod_id):
            return False
    return True


def get_all_modules_completed(session_quiz_answers):
    """Check if all Chapter 1 modules are completed."""
    return get_chapter_completion_status(session_quiz_answers, 1)


def build_pages(text: str):
    """Build a flat list of pages: Cover, TOC, then all chapters with modules, summaries, action items."""
    chapters = parse_project_outline(text)
    ch1 = extract_chapter_content(text, 1)
    ch2 = extract_chapter_content(text, 2)
    ch3 = extract_chapter_content(text, 3)
    ch4 = extract_chapter_content(text, 4)
    ch5 = extract_chapter_content(text, 5)
    ch6 = extract_chapter_content(text, 6)
    
    pages = []
    module_page_map = {}  # Maps module_id -> page_num
    quiz_page_map = {}  # Maps quiz_id -> page_num
    
    # Page 0: Cover page (lines 1-27 of project.md)
    lines = text.splitlines()
    cover_content = "\n".join(lines[0:27]) if len(lines) >= 27 else ""
    pages.append({"type": "cover", "content": cover_content, "ch1_modules": ch1["modules"], "ch2_modules": ch2["modules"], "ch3_modules": ch3["modules"], "ch4_modules": ch4["modules"], "ch5_modules": ch5["modules"], "ch6_modules": ch6["modules"]})
    
    # Page 1: Table of Contents
    pages.append({"type": "toc", "chapters": chapters, "ch1_modules": ch1["modules"], "ch2_modules": ch2["modules"], "ch3_modules": ch3["modules"], "ch4_modules": ch4["modules"], "ch5_modules": ch5["modules"], "ch6_modules": ch6["modules"]})
    
    # Chapter 1 intro
    if ch1["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 1,
            "chapter_title": ch1["chapter_title"],
            "content": ch1["intro"],
            "content_html": convert_to_html(ch1["intro"])
        })
    
    # Chapter 1 modules
    for mod in ch1["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 1,
                "chapter_title": ch1["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module
        quiz_map = {
            "1.1": MODULE_1_1_QUIZ,
            "1.2": MODULE_1_2_QUIZ,
            "1.3": MODULE_1_3_QUIZ,
            "1.4": MODULE_1_4_QUIZ,
            "1.5": MODULE_1_5_QUIZ,
            "1.6": MODULE_1_6_QUIZ,
        }
        
        if mod["id"] in quiz_map:
            quiz_questions = quiz_map[mod["id"]]
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 1,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 1 summary
    if ch1["summary"]:
        pages.append({
            "type": "summary",
            "chapter_id": 1,
            "chapter_title": ch1["chapter_title"],
            "content": ch1["summary"],
            "content_html": convert_to_html(ch1["summary"])
        })
    
    # Chapter 1 action items
    if ch1["action_items"]:
        pages.append({
            "type": "action_items",
            "chapter_id": 1,
            "chapter_title": ch1["chapter_title"],
            "content": ch1["action_items"],
            "content_html": convert_to_html(ch1["action_items"])
        })
    
    # Chapter 2 intro
    if ch2["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["intro"],
            "content_html": convert_to_html(ch2["intro"])
        })
    
    # Chapter 2 modules
    for mod in ch2["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 2,
                "chapter_title": ch2["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module
        quiz_map_ch2 = {
            "2.1": MODULE_2_1_QUIZ,
            "2.2": MODULE_2_2_QUIZ,
            "2.3": MODULE_2_3_QUIZ,
            "2.4": MODULE_2_4_QUIZ,
            "2.5": MODULE_2_5_QUIZ,
            "2.6": MODULE_2_6_QUIZ,
            "2.7": MODULE_2_7_QUIZ,
            "2.8": MODULE_2_8_QUIZ,
            "2.9": MODULE_2_9_QUIZ,
        }
        
        if mod["id"] in quiz_map_ch2:
            quiz_questions = quiz_map_ch2[mod["id"]]
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 2,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 2 summary
    if ch2["summary"]:
        pages.append({
            "type": "summary",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["summary"],
            "content_html": convert_to_html(ch2["summary"])
        })
    
    # Chapter 2 action items
    if ch2["action_items"]:
        pages.append({
            "type": "action_items",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["action_items"],
            "content_html": convert_to_html(ch2["action_items"])
        })
    
    # Chapter 3 intro
    if ch3["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 3,
            "chapter_title": ch3["chapter_title"],
            "content": ch3["intro"],
            "content_html": convert_to_html(ch3["intro"])
        })
    
    # Chapter 3 modules
    for mod in ch3["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 3,
                "chapter_title": ch3["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module
        quiz_map_ch3 = {
            "3.1": [q for q in chapter3_quizzes if q["id"].startswith("q3_1")],
            "3.2": [q for q in chapter3_quizzes if q["id"].startswith("q3_2")],
            "3.3": [q for q in chapter3_quizzes if q["id"].startswith("q3_3")],
            "3.4": [q for q in chapter3_quizzes if q["id"].startswith("q3_4")],
            "3.5": [q for q in chapter3_quizzes if q["id"].startswith("q3_5")],
            "3.6": [q for q in chapter3_quizzes if q["id"].startswith("q3_6")],
            "3.7": [q for q in chapter3_quizzes if q["id"].startswith("q3_7")],
            "3.8": [q for q in chapter3_quizzes if q["id"].startswith("q3_8")],
            "3.9": [q for q in chapter3_quizzes if q["id"].startswith("q3_9")],
        }
        
        if mod["id"] in quiz_map_ch3:
            quiz_questions = quiz_map_ch3[mod["id"]]
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 3,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 3 summary
    if ch3["summary"]:
        pages.append({
            "type": "summary",
            "chapter_id": 3,
            "chapter_title": ch3["chapter_title"],
            "content": ch3["summary"],
            "content_html": convert_to_html(ch3["summary"])
        })
    
    # Chapter 3 action items
    if ch3["action_items"]:
        pages.append({
            "type": "action_items",
            "chapter_id": 3,
            "chapter_title": ch3["chapter_title"],
            "content": ch3["action_items"],
            "content_html": convert_to_html(ch3["action_items"])
        })
    
    # Chapter 4 intro
    if ch4["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 4,
            "chapter_title": ch4["chapter_title"],
            "content": ch4["intro"],
            "content_html": convert_to_html(ch4["intro"])
        })
    
    # Chapter 4 modules
    for mod in ch4["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 4,
                "chapter_title": ch4["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module
        quiz_map_ch4 = {
            "4.1": [q for q in chapter4_quizzes if q["id"].startswith("q4_1_")],
            "4.2": [q for q in chapter4_quizzes if q["id"].startswith("q4_2_")],
            "4.3": [q for q in chapter4_quizzes if q["id"].startswith("q4_3_")],
            "4.4": [q for q in chapter4_quizzes if q["id"].startswith("q4_4_")],
            "4.5": [q for q in chapter4_quizzes if q["id"].startswith("q4_5_")],
            "4.6": [q for q in chapter4_quizzes if q["id"].startswith("q4_6_")],
            "4.7": [q for q in chapter4_quizzes if q["id"].startswith("q4_7_")],
            "4.8": [q for q in chapter4_quizzes if q["id"].startswith("q4_8_")],
            "4.9": [q for q in chapter4_quizzes if q["id"].startswith("q4_9_")],
            "4.10": [q for q in chapter4_quizzes if q["id"].startswith("q4_10_")],
            "4.11": [q for q in chapter4_quizzes if q["id"].startswith("q4_11_")],
        }
        
        if mod["id"] in quiz_map_ch4:
            quiz_questions = quiz_map_ch4[mod["id"]]
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 4,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 4 summary
    if ch4["summary"]:
        pages.append({
            "type": "summary",
            "chapter_id": 4,
            "chapter_title": ch4["chapter_title"],
            "content": ch4["summary"],
            "content_html": convert_to_html(ch4["summary"])
        })
    
    # Chapter 4 action items
    if ch4["action_items"]:
        pages.append({
            "type": "action_items",
            "chapter_id": 4,
            "chapter_title": ch4["chapter_title"],
            "content": ch4["action_items"],
            "content_html": convert_to_html(ch4["action_items"])
        })
    
    # ================================================================
    # CHAPTER 5
    # ================================================================
    
    # Chapter 5 intro
    if ch5["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 5,
            "chapter_title": ch5["chapter_title"],
            "content": ch5["intro"],
            "content_html": convert_to_html(ch5["intro"])
        })
    
    # Chapter 5 modules
    for mod in ch5["modules"]:
        module_page_map[mod["id"]] = len(pages)
        content_text = "\n".join(mod["content"])
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 5,
                "chapter_title": ch5["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module
        quiz_map_ch5 = {
            "5.1": [q for q in chapter5_quizzes if q["id"].startswith("q5_1_")],
            "5.2": [q for q in chapter5_quizzes if q["id"].startswith("q5_2_")],
            "5.3": [q for q in chapter5_quizzes if q["id"].startswith("q5_3_")],
            "5.4": [q for q in chapter5_quizzes if q["id"].startswith("q5_4_")],
            "5.5": [q for q in chapter5_quizzes if q["id"].startswith("q5_5_")],
            "5.6": [q for q in chapter5_quizzes if q["id"].startswith("q5_6_")],
            "5.7": [q for q in chapter5_quizzes if q["id"].startswith("q5_7_")],
            "5.8": [q for q in chapter5_quizzes if q["id"].startswith("q5_8_")],
            "5.9": [q for q in chapter5_quizzes if q["id"].startswith("q5_9_")],
            "5.10": [q for q in chapter5_quizzes if q["id"].startswith("q5_10_")],
        }
        
        if mod["id"] in quiz_map_ch5:
            quiz_questions = quiz_map_ch5[mod["id"]]
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)
                pages.append({
                    "type": "quiz",
                    "chapter_id": 5,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 5 summary
    if ch5["summary"]:
        pages.append({
            "type": "summary",
            "chapter_id": 5,
            "chapter_title": ch5["chapter_title"],
            "content": ch5["summary"],
            "content_html": convert_to_html(ch5["summary"])
        })
    
    # Chapter 5 action items
    if ch5["action_items"]:
        pages.append({
            "type": "action_items",
            "chapter_id": 5,
            "chapter_title": ch5["chapter_title"],
            "content": ch5["action_items"],
            "content_html": convert_to_html(ch5["action_items"])
        })
    
    # ================================================================
    # CHAPTER 6
    # ================================================================
    
    # Chapter 6 intro
    if ch6["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 6,
            "chapter_title": ch6["chapter_title"],
            "content": ch6["intro"],
            "content_html": convert_to_html(ch6["intro"])
        })
    
    # Chapter 6 modules
    for mod in ch6["modules"]:
        module_page_map[mod["id"]] = len(pages)  # Record the first page number for this module
        content_text = "\n".join(mod["content"])
        
        # Split module content into multiple pages if needed
        content_pages = split_content_into_pages(content_text)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 6,
                "chapter_title": ch6["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after the last page of each module
        quiz_map_ch6 = {
            "6.1": [q for q in chapter6_quizzes if q["id"].startswith("q6_1_")],
            "6.2": [q for q in chapter6_quizzes if q["id"].startswith("q6_2_")],
            "6.3": [q for q in chapter6_quizzes if q["id"].startswith("q6_3_")],
            "6.4": [q for q in chapter6_quizzes if q["id"].startswith("q6_4_")],
            "6.5": [q for q in chapter6_quizzes if q["id"].startswith("q6_5_")],
            "6.6": [q for q in chapter6_quizzes if q["id"].startswith("q6_6_")],
            "6.7": [q for q in chapter6_quizzes if q["id"].startswith("q6_7_")],
            "6.8": [q for q in chapter6_quizzes if q["id"].startswith("q6_8_")],
            "6.9": [q for q in chapter6_quizzes if q["id"].startswith("q6_9_")],
            "6.10": [q for q in chapter6_quizzes if q["id"].startswith("q6_10_")],
            "6.11": [q for q in chapter6_quizzes if q["id"].startswith("q6_11_")],
        }
        
        if mod["id"] in quiz_map_ch6:
            quiz_questions = quiz_map_ch6[mod["id"]]
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)  # Track quiz question page number
                pages.append({
                    "type": "quiz",
                    "chapter_id": 6,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 6 summary
    if ch6["summary"]:
        pages.append({
            "type": "summary",
            "chapter_id": 6,
            "chapter_title": ch6["chapter_title"],
            "content": ch6["summary"],
            "content_html": convert_to_html(ch6["summary"])
        })
    
    # Chapter 6 action items
    if ch6["action_items"]:
        pages.append({
            "type": "action_items",
            "chapter_id": 6,
            "chapter_title": ch6["chapter_title"],
            "content": ch6["action_items"],
            "content_html": convert_to_html(ch6["action_items"])
        })
    
    # Add module_page_map and quiz_page_map to cover and TOC pages
    pages[0]["module_page_map"] = module_page_map
    pages[0]["quiz_page_map"] = quiz_page_map
    pages[1]["module_page_map"] = module_page_map
    pages[1]["quiz_page_map"] = quiz_page_map
    
    # Note: Glossary is now a separate page at /glossary, not part of page navigation
    
    print(f"[build_pages] Built {len(pages)} pages")
    return pages


@app.route("/")
def index():
    return redirect(url_for("page", page_num=0))


@app.route("/page/<int:page_num>", methods=["GET", "POST"])
def page(page_num: int):
    try:
        text = PROJECT_MD_PATH.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        text = ""
    
    pages = build_pages(text) if text else []
    
    if page_num < 0 or page_num >= len(pages):
        page_num = 0
    
    current_page = pages[page_num] if pages else {"type": "error", "content": "No content found"}
    
    # Initialize session for quiz answers if not exists
    if 'quiz_answers' not in session:
        session['quiz_answers'] = {}
    
    # Check for preview mode query parameter
    if request.args.get('preview') == 'true':
        session['preview_mode'] = True
    elif 'preview' in request.args and request.args.get('preview') == 'false':
        session['preview_mode'] = False
    
    # Handle quiz answer submission
    quiz_feedback = None
    if request.method == "POST" and current_page.get("type") == "quiz":
        selected_answer = request.form.get("answer")
        if selected_answer is not None:
            selected_index = int(selected_answer)
            quiz_question = current_page["quiz_question"]
            correct_index = quiz_question["correct_index"]
            
            if selected_index == correct_index:
                # Correct answer - mark as answered and allow progression
                session['quiz_answers'][quiz_question["id"]] = True
                session.modified = True
                quiz_feedback = {
                    "correct": True,
                    "message": "Correct! " + quiz_question["explanation"]
                }
            else:
                # Incorrect answer
                quiz_feedback = {
                    "correct": False,
                    "message": "That's not quite right. Please try again.",
                    "selected_index": selected_index
                }
    
    # Check if current quiz question has been answered correctly
    quiz_answered = False
    if current_page.get("type") == "quiz":
        quiz_id = current_page["quiz_question"]["id"]
        quiz_answered = session['quiz_answers'].get(quiz_id, False)
    
    prev_num = page_num - 1 if page_num > 0 else None
    
    # Check if in preview mode (bypasses all locks for content creators)
    preview_mode = session.get('preview_mode', False)
    
    # Only allow next if not a quiz OR quiz has been answered correctly (or in preview mode)
    next_allowed = True
    if current_page.get("type") == "quiz" and not quiz_answered and not preview_mode:
        next_allowed = False
    
    # Check if trying to access a locked page (module/summary/action_items)
    if not preview_mode and current_page.get("type") == "module":
        # Check if previous modules are complete
        current_module_id = current_page.get("module_id")
        if current_module_id:
            # Define module sequences for each chapter
            chapter_1_modules = ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"]
            chapter_2_modules = ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"]
            chapter_3_modules = ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9"]
            chapter_4_modules = ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9", "4.10", "4.11"]
            
            # Determine which chapter and check previous modules
            if current_module_id.startswith("1."):
                module_index = chapter_1_modules.index(current_module_id) if current_module_id in chapter_1_modules else 0
                if module_index > 0:
                    for i in range(module_index):
                        if not get_module_completion_status(session.get('quiz_answers', {}), chapter_1_modules[i]):
                            return redirect(url_for("page", page_num=1))
            elif current_module_id.startswith("2."):
                # For Chapter 2, first check if all Chapter 1 is complete
                if not get_chapter_completion_status(session.get('quiz_answers', {}), 1):
                    return redirect(url_for("page", page_num=1))
                # Then check previous Chapter 2 modules
                module_index = chapter_2_modules.index(current_module_id) if current_module_id in chapter_2_modules else 0
                if module_index > 0:
                    for i in range(module_index):
                        if not get_module_completion_status(session.get('quiz_answers', {}), chapter_2_modules[i]):
                            return redirect(url_for("page", page_num=1))
            elif current_module_id.startswith("3."):
                # For Chapter 3, first check if all Chapter 2 is complete
                if not get_chapter_completion_status(session.get('quiz_answers', {}), 2):
                    return redirect(url_for("page", page_num=1))
                # Then check previous Chapter 3 modules
                module_index = chapter_3_modules.index(current_module_id) if current_module_id in chapter_3_modules else 0
                if module_index > 0:
                    for i in range(module_index):
                        if not get_module_completion_status(session.get('quiz_answers', {}), chapter_3_modules[i]):
                            return redirect(url_for("page", page_num=1))
            elif current_module_id.startswith("4."):
                # For Chapter 4, first check if all Chapter 3 is complete
                if not get_chapter_completion_status(session.get('quiz_answers', {}), 3):
                    return redirect(url_for("page", page_num=1))
                # Then check previous Chapter 4 modules
                module_index = chapter_4_modules.index(current_module_id) if current_module_id in chapter_4_modules else 0
                if module_index > 0:
                    for i in range(module_index):
                        if not get_module_completion_status(session.get('quiz_answers', {}), chapter_4_modules[i]):
                            return redirect(url_for("page", page_num=1))
            elif current_module_id.startswith("5."):
                # For Chapter 5, first check if all Chapter 4 is complete
                if not get_chapter_completion_status(session.get('quiz_answers', {}), 4):
                    return redirect(url_for("page", page_num=1))
                # Then check previous Chapter 5 modules
                chapter_5_modules = ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9", "5.10"]
                module_index = chapter_5_modules.index(current_module_id) if current_module_id in chapter_5_modules else 0
                if module_index > 0:
                    for i in range(module_index):
                        if not get_module_completion_status(session.get('quiz_answers', {}), chapter_5_modules[i]):
                            return redirect(url_for("page", page_num=1))
            elif current_module_id.startswith("6."):
                # For Chapter 6, first check if all Chapter 5 is complete
                if not get_chapter_completion_status(session.get('quiz_answers', {}), 5):
                    return redirect(url_for("page", page_num=1))
                # Then check previous Chapter 6 modules
                chapter_6_modules = ["6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "6.8", "6.9", "6.10", "6.11"]
                module_index = chapter_6_modules.index(current_module_id) if current_module_id in chapter_6_modules else 0
                if module_index > 0:
                    for i in range(module_index):
                        if not get_module_completion_status(session.get('quiz_answers', {}), chapter_6_modules[i]):
                            return redirect(url_for("page", page_num=1))
    
    # Lock summary and action items until all modules complete (unless in preview mode)
    if not preview_mode and current_page.get("type") in ["summary", "action_items"]:
        chapter_id = current_page.get("chapter_id", 1)
        if not get_chapter_completion_status(session.get('quiz_answers', {}), chapter_id):
            # Redirect to TOC if trying to access locked summary/action items
            return redirect(url_for("page", page_num=1))
    
    next_num = page_num + 1 if page_num < len(pages) - 1 and next_allowed else None
    
    # Get module-specific page counter from page data (resets per module)
    module_page_num = None
    module_total_pages = None
    
    if current_page.get("type") == "module":
        # Multi-page module support
        module_page_num = current_page.get("module_page_num", 1)
        module_total_pages = current_page.get("module_total_pages", 1)
    elif current_page.get("type") in ["intro", "summary", "action_items"]:
        # Single-page sections
        module_page_num = 1
        module_total_pages = 1
    
    # Check module completion status
    module_completion = {}
    all_ch1_modules_complete = False
    all_ch2_modules_complete = False
    all_ch3_modules_complete = False
    all_ch4_modules_complete = False
    all_ch5_modules_complete = False
    all_ch6_modules_complete = False
    if pages:
        # Get modules from all chapters' data stored in pages
        ch1_modules = pages[0].get("ch1_modules", [])
        ch2_modules = pages[0].get("ch2_modules", [])
        ch3_modules = pages[0].get("ch3_modules", [])
        ch4_modules = pages[0].get("ch4_modules", [])
        ch5_modules = pages[0].get("ch5_modules", [])
        ch6_modules = pages[0].get("ch6_modules", [])
        
        for mod in ch1_modules:
            module_completion[mod["id"]] = get_module_completion_status(session.get('quiz_answers', {}), mod["id"])
        all_ch1_modules_complete = get_chapter_completion_status(session.get('quiz_answers', {}), 1)
        
        for mod in ch2_modules:
            module_completion[mod["id"]] = get_module_completion_status(session.get('quiz_answers', {}), mod["id"])
        all_ch2_modules_complete = get_chapter_completion_status(session.get('quiz_answers', {}), 2)
        
        for mod in ch3_modules:
            module_completion[mod["id"]] = get_module_completion_status(session.get('quiz_answers', {}), mod["id"])
        all_ch3_modules_complete = get_chapter_completion_status(session.get('quiz_answers', {}), 3)
        
        for mod in ch4_modules:
            module_completion[mod["id"]] = get_module_completion_status(session.get('quiz_answers', {}), mod["id"])
        all_ch4_modules_complete = get_chapter_completion_status(session.get('quiz_answers', {}), 4)
        
        for mod in ch5_modules:
            module_completion[mod["id"]] = get_module_completion_status(session.get('quiz_answers', {}), mod["id"])
        all_ch5_modules_complete = get_chapter_completion_status(session.get('quiz_answers', {}), 5)
        
        for mod in ch6_modules:
            module_completion[mod["id"]] = get_module_completion_status(session.get('quiz_answers', {}), mod["id"])
        all_ch6_modules_complete = get_chapter_completion_status(session.get('quiz_answers', {}), 6)
    
    # Quiz map for TOC dropdown display
    quiz_map = {
        "1.1": MODULE_1_1_QUIZ,
        "1.2": MODULE_1_2_QUIZ,
        "1.3": MODULE_1_3_QUIZ,
        "1.4": MODULE_1_4_QUIZ,
        "1.5": MODULE_1_5_QUIZ,
        "1.6": MODULE_1_6_QUIZ,
        "2.1": MODULE_2_1_QUIZ,
        "2.2": MODULE_2_2_QUIZ,
        "2.3": MODULE_2_3_QUIZ,
        "2.4": MODULE_2_4_QUIZ,
        "2.5": MODULE_2_5_QUIZ,
        "2.6": MODULE_2_6_QUIZ,
        "2.7": MODULE_2_7_QUIZ,
        "2.8": MODULE_2_8_QUIZ,
        "2.9": MODULE_2_9_QUIZ,
        "3.1": [q for q in chapter3_quizzes if q["id"].startswith("q3_1")],
        "3.2": [q for q in chapter3_quizzes if q["id"].startswith("q3_2")],
        "3.3": [q for q in chapter3_quizzes if q["id"].startswith("q3_3")],
        "3.4": [q for q in chapter3_quizzes if q["id"].startswith("q3_4")],
        "3.5": [q for q in chapter3_quizzes if q["id"].startswith("q3_5")],
        "3.6": [q for q in chapter3_quizzes if q["id"].startswith("q3_6")],
        "3.7": [q for q in chapter3_quizzes if q["id"].startswith("q3_7")],
        "3.8": [q for q in chapter3_quizzes if q["id"].startswith("q3_8")],
        "3.9": [q for q in chapter3_quizzes if q["id"].startswith("q3_9")],
        "4.1": [q for q in chapter4_quizzes if q["id"].startswith("q4_1_")],
        "4.2": [q for q in chapter4_quizzes if q["id"].startswith("q4_2_")],
        "4.3": [q for q in chapter4_quizzes if q["id"].startswith("q4_3_")],
        "4.4": [q for q in chapter4_quizzes if q["id"].startswith("q4_4_")],
        "4.5": [q for q in chapter4_quizzes if q["id"].startswith("q4_5_")],
        "4.6": [q for q in chapter4_quizzes if q["id"].startswith("q4_6_")],
        "4.7": [q for q in chapter4_quizzes if q["id"].startswith("q4_7_")],
        "4.8": [q for q in chapter4_quizzes if q["id"].startswith("q4_8_")],
        "4.9": [q for q in chapter4_quizzes if q["id"].startswith("q4_9_")],
        "4.10": [q for q in chapter4_quizzes if q["id"].startswith("q4_10_")],
        "4.11": [q for q in chapter4_quizzes if q["id"].startswith("q4_11_")],
        "5.1": [q for q in chapter5_quizzes if q["id"].startswith("q5_1_")],
        "5.2": [q for q in chapter5_quizzes if q["id"].startswith("q5_2_")],
        "5.3": [q for q in chapter5_quizzes if q["id"].startswith("q5_3_")],
        "5.4": [q for q in chapter5_quizzes if q["id"].startswith("q5_4_")],
        "5.5": [q for q in chapter5_quizzes if q["id"].startswith("q5_5_")],
        "5.6": [q for q in chapter5_quizzes if q["id"].startswith("q5_6_")],
        "5.7": [q for q in chapter5_quizzes if q["id"].startswith("q5_7_")],
        "5.8": [q for q in chapter5_quizzes if q["id"].startswith("q5_8_")],
        "5.9": [q for q in chapter5_quizzes if q["id"].startswith("q5_9_")],
        "5.10": [q for q in chapter5_quizzes if q["id"].startswith("q5_10_")],
        "6.1": [q for q in chapter6_quizzes if q["id"].startswith("q6_1_")],
        "6.2": [q for q in chapter6_quizzes if q["id"].startswith("q6_2_")],
        "6.3": [q for q in chapter6_quizzes if q["id"].startswith("q6_3_")],
        "6.4": [q for q in chapter6_quizzes if q["id"].startswith("q6_4_")],
        "6.5": [q for q in chapter6_quizzes if q["id"].startswith("q6_5_")],
        "6.6": [q for q in chapter6_quizzes if q["id"].startswith("q6_6_")],
        "6.7": [q for q in chapter6_quizzes if q["id"].startswith("q6_7_")],
        "6.8": [q for q in chapter6_quizzes if q["id"].startswith("q6_8_")],
        "6.9": [q for q in chapter6_quizzes if q["id"].startswith("q6_9_")],
        "6.10": [q for q in chapter6_quizzes if q["id"].startswith("q6_10_")],
        "6.11": [q for q in chapter6_quizzes if q["id"].startswith("q6_11_")],
    }
    
    return render_template(
        "page.html",
        page=current_page,
        page_num=page_num,
        total_pages=len(pages),
        prev_num=prev_num,
        next_num=next_num,
        quiz_feedback=quiz_feedback,
        quiz_answered=quiz_answered,
        module_page_num=module_page_num,
        module_total_pages=module_total_pages,
        module_completion=module_completion,
        all_ch1_modules_complete=all_ch1_modules_complete,
        all_ch2_modules_complete=all_ch2_modules_complete,
        all_ch3_modules_complete=all_ch3_modules_complete,
        all_ch4_modules_complete=all_ch4_modules_complete,
        all_ch5_modules_complete=all_ch5_modules_complete,
        all_ch6_modules_complete=all_ch6_modules_complete,
        preview_mode=preview_mode,
        quiz_map=quiz_map,
        quiz_answers=session.get('quiz_answers', {})
    )


@app.route("/glossary")
def glossary():
    try:
        text = PROJECT_MD_PATH.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        text = ""
    
    glossary_terms = parse_glossary_terms(text) if text else []
    
    return render_template(
        "glossary.html",
        glossary_terms=glossary_terms
    )


@app.route("/reset")
def reset():
    """Reset all quiz progress and redirect to home."""
    session.clear()
    return redirect(url_for("page", page_num=0))


@app.route("/preview")
def preview():
    """Enable preview mode - unlocks all content for creators to review."""
    session['preview_mode'] = True
    return redirect(url_for("page", page_num=1))


if __name__ == "__main__":
    app.run(debug=True)
