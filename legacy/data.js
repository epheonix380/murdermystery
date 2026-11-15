// The Last Chapter at Hollowpine Lodge — all game content.
// Edit text here; index.html renders it. Codes are not secure on purpose.

window.CASE = {
  title: "The Last Chapter at Hollowpine Lodge",
  gmCode: "RAVEN",
  round2Code: "STORM",

  premise: [
    "Every Halloween, horror novelist Edgar Thorne throws a costume party at Hollowpine Lodge, his mountain retreat.",
    "Tonight he promised a surprise: at the midnight unmasking he would read the final chapter of his unpublished novel, The Last Chapter. \"Some of you,\" he said at dinner, \"will recognize yourselves.\"",
    "At 11:15 PM a storm cut the power. At 11:20 a scream came from the study. When the lights came back at 11:30, Edgar was dead on his study floor, and his manuscript was gone.",
    "The roads are flooded. Nobody leaves until the killer is named."
  ],

  rules: [
    "Talk, question, accuse, bargain and lie as much as you like.",
    "Everything on your sheet can be shared, or hidden. Your call.",
    "The one thing you can never reveal is your secret goal.",
    "Item cards change hands only when the holder hands them over. No snatching.",
    "At the end everyone secretly votes for the killer. Catch them and the group wins. Meet your secret goal and you win a bonus prize too."
  ],

  // ---------- PLAYER SHEETS ----------
  roles: {
    WOLF: {
      name: "Marcus Reed",
      costume: "Werewolf (mask, furry gloves, rubber paw feet)",
      core: true,
      killer: true,
      who: "Edgar's business partner. You run the lodge's money and his publishing company's books.",
      attitude: "Jolly, loud, everybody's buddy. You get defensive about money.",
      cornered: "\"I was out in the rain having a smoke! Ask anyone how soaked I was!\"",
      goal: "Don't get the most votes. If the group votes for anyone else, you win.",
      secret: "You are the killer. You've quietly taken $340,000 from the business. Edgar found out and wrote you into Chapter 13 as a \"werewolf accountant.\"",
      timeline: [
        ["7:15", "Study", "Arrived early. Edgar showed you an audit: confess to everyone by midnight, or he reads Chapter 13 aloud and calls his lawyer. He also bragged he'd changed his will to leave the lodge to \"the only one who never asked me for anything.\"", "hide"],
        ["7:30", "Foyer", "The other guests arrive."],
        ["8:30", "Dining Room", "Dinner. Edgar's toast: at midnight he reads Chapter 13."],
        ["8:30–10:40", "Great Room", "Drinks with Vivian and Julian. Very chatty."],
        ["10:40", "Kitchen", "Announced a smoke break and walked out through the kitchen."],
        ["10:42", "Mudroom", "Out the back door in full costume. Ruth saw you go."],
        ["10:45", "Back Porch → Study", "Walked along the porch and in through the study's French doors. You argued.", "hide"],
        ["10:50", "Study", "Struck Edgar on the back of the head with his Golden Raven award.", "hide"],
        ["10:52", "Study", "Burned Chapter 13 in the fireplace. Set Edgar's sound-effects recorder (in the skull on the shelf) to play a scream at 11:20. Wound his watch to 11:20 and smashed it.", "hide"],
        ["10:58", "Mudroom", "Out the French doors with the manuscript and the award. Hid both, wrapped in a towel, in the umbrella stand.", "hide"],
        ["11:00", "Kitchen → upstairs", "Crossed the empty kitchen to the back stairs. Stuffed your muddy paw feet in your bag and put on sneakers.", "hide"],
        ["11:02", "Great Room", "Came back with your mask off and wet hair: \"Rain's picked up!\""],
        ["11:06", "Great Room", "Photo booth with Vivian and Julian."],
        ["11:10", "Great Room", "Started a loud ghost-story game so everyone stayed close to you."],
        ["11:15", "Great Room", "Blackout."],
        ["11:20", "Great Room", "Squeezed Vivian's arm a second before the scream: \"Stay close, Viv.\""],
        ["11:32", "Study", "Vivian finds the body."]
      ],
      story: [
        "You arrived with everyone else at 7:30.",
        "10:40 to 11:02 you were on the back porch smoking and watching the storm. You never went near the study.",
        "You took off the paw feet upstairs because they were soaked and squelching.",
        "At 11:20 you were in the Great Room with Vivian. She can vouch for you."
      ],
      others: [
        ["Ruth", "Edgar told you he changed his will to leave the lodge to someone. Ruth has keys to everything and was off alone a lot tonight."],
        ["Julian", "Always asking Edgar for money. He disappeared outside during the blackout."],
        ["Vivian", "Furious that Edgar never gave her credit for her editing."]
      ],
      tips: [
        "The group will focus on the blackout. Keep them there. Your 11:20 alibi is perfect.",
        "If they work out the time of death was earlier, point at Ruth: alone in the kitchen, then off to her cabin.",
        "If they find your paw feet, say anyone could have borrowed them while they dried."
      ]
    },

    BREW: {
      name: "Vivian Thorne",
      costume: "Witch (dark purple lipstick)",
      core: true,
      who: "Edgar's ex-wife, and still his editor.",
      attitude: "Sharp, dry, unimpressed by everyone.",
      cornered: "\"I edited that man for twenty years. If I'd wanted him dead, he'd have been dead in 2009.\"",
      goal: "Be holding the Manuscript card when the game ends.",
      secret: "You secretly ghostwrote Edgar's last three books. He refused to credit you. Your handwriting all over the manuscript proves it, so you want it back.",
      timeline: [
        ["7:30", "Foyer", "Arrived."],
        ["8:30", "Dining Room", "Dinner. Edgar's toast about Chapter 13."],
        ["9:40", "Study", "Demanded co-author credit. Edgar laughed it off. You drank a glass of wine there."],
        ["10:00–11:32", "Great Room", "Back with Julian and Marcus. You stayed here the whole time."],
        ["10:40", "Great Room", "Marcus left for a \"smoke break\" through the kitchen."],
        ["10:50", "Great Room", "Julian went to the kitchen for ice. Back by 10:52."],
        ["10:55", "Great Room", "Texted Edgar: \"Are you reading it at midnight or not?\" No reply."],
        ["11:02", "Great Room", "Marcus came back soaked, mask off, wearing sneakers instead of his paw feet."],
        ["11:06", "Great Room", "Photo booth with Marcus and Julian."],
        ["11:12", "Great Room", "Julian stepped outside to make a call."],
        ["11:20", "Great Room", "A second before the scream, Marcus squeezed your arm: \"Stay close, Viv.\" It felt odd, like he was expecting it."],
        ["11:32", "Study", "Went to ask Edgar about the reading and found him dead. You spent 30 seconds searching his desk for the manuscript before calling for help.", "hide"]
      ],
      others: [
        ["Ruth", "Has been at the lodge forever. Edgar trusted her more than he ever trusted you."],
        ["Julian", "Edgar's nephew. Always broke."],
        ["Graham (if playing)", "A rival author who has hated Edgar for decades."]
      ],
      tips: [
        "You were in the Great Room all night. That's a strong alibi. Use it.",
        "Whoever finds the manuscript, make a deal with them. What do they want?",
        "The arm squeeze is a real clue. Share it when it helps you."
      ]
    },

    FANG: {
      name: "Julian Thorne",
      costume: "Vampire",
      core: true,
      who: "Edgar's nephew. Charming, broke, and in trouble.",
      attitude: "Nervous charm. Jokes when stressed.",
      cornered: "\"I'm family! Why would I kill the only person who might still lend me money?\"",
      goal: "Ruth must get at least 2 votes at the end.",
      secret: "You owe a bookie, Lucky Lou, $28,000 by November 1. Tonight you stole $500 from Edgar's wallet. And Edgar told you his new will leaves the lodge to Ruth, the caretaker.",
      timeline: [
        ["7:30", "Foyer", "Arrived."],
        ["8:30", "Dining Room", "Dinner. Edgar's toast about Chapter 13."],
        ["9:15", "Study", "Asked Edgar for money. He refused, and said his new will leaves the lodge to Ruth."],
        ["9:30", "Study", "Took $500 from Edgar's wallet while his back was turned.", "hide"],
        ["9:30–10:50", "Great Room", "Drinks with Vivian, and Marcus until 10:40."],
        ["10:40", "Great Room", "Marcus left for a smoke through the kitchen."],
        ["10:50", "Kitchen", "Went for ice. Ruth was there chopping snacks; you chatted for 2 minutes. The kitchen floor was clean."],
        ["10:52", "Great Room", "Back with Vivian."],
        ["11:02", "Great Room", "Marcus came back with wet hair, in sneakers."],
        ["11:06", "Great Room", "Photo booth with Marcus and Vivian."],
        ["11:12", "Front Porch", "Stepped out to call Lucky Lou. Your phone shows the call ran 11:13–11:21.", "hide"],
        ["11:15", "Front Porch", "Blackout. You didn't hear any scream over the storm."],
        ["11:24", "Foyer", "Came back in, soaked."],
        ["11:34", "Study", "Everyone gathers at the body."]
      ],
      others: [
        ["Ruth", "Gets the whole lodge in the new will. Convenient for her that Edgar died tonight."],
        ["Marcus", "Edgar's money guy. Was gone a long time for one cigarette."],
        ["Vivian", "Edgar's ex. Still bitter."]
      ],
      tips: [
        "Your call log clears you at 11:20, but sharing it reveals your debts. Choose when.",
        "Steer suspicion toward Ruth: the will, the keys, the breaker box.",
        "The clean kitchen floor at 10:50 is worth remembering."
      ]
    },

    KEYS: {
      name: "Ruth Kowalski",
      costume: "No costume. \"I work here.\"",
      core: true,
      who: "Caretaker of Hollowpine Lodge for 28 years. You have a key to every door.",
      attitude: "Practical, blunt, protective of the lodge.",
      cornered: "\"I know every creaky board in this lodge, and I was nowhere near that study.\"",
      goal: "Be holding the 1998 Photo card when the game ends.",
      secret: "In the summer of 1998 you and Edgar had a secret romance, while he was married to Vivian. He's leaving you the lodge, and you already knew: he told you in a letter.",
      timeline: [
        ["6:00", "Whole lodge", "Finished setting up the party."],
        ["7:15", "Hallway", "Walking past the study, you heard Edgar and Marcus arguing. You caught the word \"midnight.\""],
        ["8:30", "Dining Room", "Served dinner."],
        ["10:30", "Kitchen", "Started midnight snacks and tea."],
        ["10:42", "Kitchen", "Saw Marcus go out the back door in full costume, paw feet and all."],
        ["10:44", "Kitchen", "Edgar texted you: \"Tea at 11 please.\""],
        ["10:50", "Kitchen", "Julian came in for ice. You chatted for 2 minutes."],
        ["10:55", "Ruth's Cabin", "Went to your cabin for candles."],
        ["11:05", "Kitchen", "Back. Someone had tracked muddy paw prints across your clean floor to the back stairs. Annoying. You moved the tea to 11:15."],
        ["11:15", "Kitchen", "Blackout."],
        ["11:18", "Mudroom", "Checked the breaker box by flashlight. Nothing had tripped. The power line was down."],
        ["11:20", "Mudroom", "Heard the scream from here."],
        ["11:28", "Outside", "Started the backup generator and logged it."],
        ["11:30", "Mudroom", "Power back."]
      ],
      others: [
        ["Marcus", "Arguing with Edgar at 7:15. Went out the back door at 10:42 for a long \"smoke.\""],
        ["Julian", "Came to the kitchen at 10:50. Always sniffing around Edgar's money."],
        ["Vivian", "If she ever learns about 1998, she'll make your life miserable."]
      ],
      tips: [
        "You look suspicious: keys, the breaker box, alone a lot, and the will. Expect accusations.",
        "Your strongest facts: Julian saw you at 10:50, and you saw Marcus leave at 10:42.",
        "The 1998 photo is in Edgar's safe. Whoever opens it, be ready to bargain."
      ]
    },

    ROT: {
      name: "Graham Pike",
      costume: "Zombie",
      core: false,
      who: "A rival horror author. You and Edgar have hated each other for 25 years.",
      attitude: "Grumpy and theatrical. Everything is a conspiracy against you.",
      cornered: "\"If I killed every hack who stole from me, there'd be no one left in publishing.\"",
      goal: "Be holding the Manuscript card when the game ends.",
      secret: "You believe Edgar's first hit, The Hollowpine Girl, was copied from your unpublished 1996 book The Hollow Girl. Tonight you threw a threatening note at him.",
      timeline: [
        ["7:30", "Foyer", "Arrived. Only came because the press would be here."],
        ["8:30", "Dining Room", "Dinner. Edgar's toast about Chapter 13."],
        ["10:05", "Study", "Barged in and accused Edgar of stealing your story. Threw a note at him: \"You'll pay for it.\" He laughed."],
        ["10:10", "Great Room", "Sulked at the bar."],
        ["10:30–11:32", "Dining Room", "Helped Madame Oriel set up her séance table. You were together the whole time."],
        ["11:20", "Dining Room", "Heard the scream. Oriel grabbed your hand."]
      ],
      others: [
        ["Madame Oriel", "With you in the Dining Room from 10:30. Seemed more nervous than spooky."],
        ["Vivian", "Edgar's editor. You suspect she wrote more of his books than he did."]
      ],
      tips: [
        "Your note looks bad. Your alibi with Oriel is good.",
        "You want the manuscript to prove Edgar stole from you. So does Vivian, for her own reasons."
      ]
    },

    ORB: {
      name: "Madame Oriel",
      costume: "Psychic (shawl, crystal ball)",
      core: false,
      who: "A psychic medium hired to run a midnight séance.",
      attitude: "Mysterious and dramatic, with a slightly fake accent.",
      cornered: "\"The spirits do not lie, darling. People do.\"",
      goal: "Get the group to hold your séance before the final vote. (Ask the GM to run it. The GM speaks as Edgar's ghost.)",
      secret: "Your real name is Doreen Fisk. You were Edgar's assistant from 2014 until he fired you in 2019. Your \"spirit voices\" come from a Bluetooth speaker taped under the table.",
      timeline: [
        ["7:30", "Foyer", "Arrived with your crystal ball."],
        ["8:30", "Dining Room", "Dinner. Edgar didn't recognize you, or pretended not to."],
        ["10:30", "Dining Room", "Started setting up the séance. Asked Ruth for more candles. Graham helped you."],
        ["10:30–11:32", "Dining Room", "With Graham the whole time."],
        ["11:20", "Dining Room", "The scream. Not your speaker. You checked your phone to be sure."]
      ],
      others: [
        ["Edgar", "From your years as his assistant: he used a little voice recorder for sound effects constantly. He recorded screams for his audiobooks."],
        ["Graham", "With you in the Dining Room from 10:30."],
        ["Ruth", "Fetched the candles you asked for."]
      ],
      tips: [
        "Play up the mystic act. It's your best cover.",
        "What you know about Edgar's recorder could crack the case. Decide when to share it.",
        "Push for the séance. The GM will give the group a ghostly hint."
      ]
    },

    BOO: {
      name: "Penny Lark",
      costume: "Bedsheet ghost",
      core: false,
      who: "Edgar's biggest fan and a horror blogger. You weren't invited.",
      attitude: "Starstruck and excitable. Treats everything like content.",
      cornered: "\"I'm a JOURNALIST. Kind of. I have 4,000 followers!\"",
      goal: "Your final vote must be for the real killer.",
      secret: "You sneaked onto the property and hid inside the lodge for over an hour.",
      timeline: [
        ["9:00", "Back Porch", "Sneaked onto the covered back porch to catch a glimpse of Edgar."],
        ["10:22", "Back Porch", "Took a photo of Edgar typing at his desk through the study window. He was very much alive."],
        ["10:28", "Hallway", "Slipped inside and hid in the hallway coat closet, right next to the study."],
        ["10:45–10:50", "Coat closet", "Heard muffled voices through the wall, then a heavy thud. You assumed it was a party game."],
        ["11:20", "Coat closet", "The scream came from right next door. It sounded tinny, like it was coming out of a speaker. No footsteps before or after."],
        ["11:34", "Hallway", "Got caught sneaking out of the closet."]
      ],
      others: [
        ["Edgar", "You've read everything he wrote. He always talked about recording his own sound effects."]
      ],
      tips: [
        "You're the one person who wasn't at the party, so everyone will suspect you.",
        "Your photo and what you heard are powerful. Share them to clear yourself, then solve it."
      ]
    }
  },

  // ---------- BODY HOTSPOTS ----------
  // round: 1 visible from start, 2 needs the Round 2 code
  body: [
    { id: "B1", round: 1, label: "Back of head", text: "A heavy blunt wound to the back of the head. He was struck from behind, by someone he'd turned his back on." },
    { id: "B2", round: 1, label: "Left wrist", text: "His wristwatch face is smashed. The hands are stopped at 11:20." },
    { id: "B3", round: 1, label: "Phone", text: "Last message sent 10:44 PM, to Ruth: \"Tea at 11 please.\" Every message from 10:55 PM on is unread, including Vivian at 10:55: \"Are you reading it at midnight or not?\"" },
    { id: "B4", round: 1, label: "Wallet", text: "His wallet is empty except for a few receipts." },
    { id: "B5", round: 1, label: "Left cuff", text: "Strands of coarse gray fur caught on his left cuff." },
    { id: "B6", round: 2, label: "Watch, up close", text: "Look closer: the watch crown is pulled out. Someone set the time by hand before smashing it." },
    { id: "B7", round: 2, label: "Coroner's note", text: "The Deputy's coroner note: the blood had dried and the body had cooled. Death happened between 10:45 and 11:05 PM." },
    { id: "B8", round: 2, label: "Inside jacket pocket", text: "An index card: \"Midnight: read Ch. 13 unless the wolf comes clean.\"" }
  ],

  // ---------- PUZZLES ----------
  puzzles: [
    {
      id: "safe",
      title: "The Safe",
      prompt: "Edgar's safe needs a 6-digit code. Find the clues that tell you what it is.",
      hint: "Edgar always said everything started with his first book.",
      unlocks: "EDGAR'S SAFE",
      check: function (v) { var d = v.replace(/\D/g, ""); return d === "103198" || d === "10311998"; }
    },
    {
      id: "page",
      title: "The Burnt Page",
      prompt: "Decode the burnt page from the fireplace. Type the LAST word of the message.",
      hint: "Count the birds in the painting.",
      unlocks: "GUEST ROOMS",
      check: function (v) { return /\bSIGHT\b/i.test(v.trim()); }
    },
    {
      id: "route",
      title: "The Route",
      prompt: "The Great Room was crowded all night, yet nobody saw the killer reach the study. Starting from the Great Room, tap the rooms the killer passed through, in order, ending at the Study.",
      hint: "Is there another way into the study?",
      unlocks: "THE UMBRELLA STAND (Mudroom)",
      route: ["kitchen", "mudroom", "porch", "study"]
    }
  ],

  cipher: "WKH ZHUHZROI FRXQWHG WKH JROG WZLFH DQG NHSW LW RQFH. KH QHYHU OHW KLV EDJ RXW RI KLV VLJKW.",

  // ---------- CLUE CARDS (for printing) ----------
  // opt: which optional role the card belongs to (pull it if that role isn't played)
  cards: [
    { id: "C01", loc: "Study", round: 1, text: "A plastic skull on the bookshelf is hollow. Inside: Edgar's digital voice recorder, labeled \"E. Thorne - sound effects\". Its timer was set for 11:20 PM. Last file played: SCREAM_07." },
    { id: "C02", loc: "Study", round: 1, text: "A clean rectangle in the dust on the shelf, where Edgar's Golden Raven award always stood. The award is gone." },
    { id: "C03", loc: "Study", round: 1, text: "The French doors to the back porch are unlocked. A tuft of coarse gray fur is caught on the latch." },
    { id: "C04", loc: "Study", round: 1, text: "One muddy print on the rug just inside the French doors. Not a shoe. It looks like a big animal paw." },
    { id: "C05", loc: "Study", round: 1, cipher: true, text: "A half-burnt page pulled from the fireplace. The surviving lines are written in some kind of code:" },
    { id: "C06", loc: "Study", round: 1, text: "A painting over the fireplace: \"Three Ravens at Midnight\". Edgar used to call it \"my key to everything.\"" },
    { id: "C07", loc: "Study", round: 1, text: "A sticky note under the desk drawer, in Edgar's handwriting: \"Safe = the night it all began.\"" },
    { id: "C08", loc: "Study", round: 1, text: "A wine glass on the side table, with dark purple lipstick on the rim." },
    { id: "C09", loc: "Study", round: 1, opt: "ROT", text: "A crumpled note in the wastebasket: \"You stole my story. You'll pay for it. -G.P.\"" },
    { id: "C10", loc: "Great Room", round: 1, text: "A framed book cover on the wall: The Hollowpine Girl, Edgar's first bestseller. Small print: \"First published October 31, 1998.\"" },
    { id: "C11", loc: "Great Room", round: 1, text: "A photo booth strip stamped 11:06 PM: Marcus, Vivian and Julian pulling faces. Marcus has wet hair, his werewolf mask in his hand, and sneakers on instead of his paw feet." },
    { id: "C12", loc: "Great Room", round: 1, text: "Party schedule on the mantel: 8:00 Drinks. 8:30 Dinner. Midnight: Unmasking, and Edgar reads Chapter 13." },
    { id: "C13", loc: "Kitchen", round: 1, text: "A tea tray, set and untouched. Ruth's note: \"Mr. T tea - 11:00\", with 11:00 crossed out and 11:15 written in." },
    { id: "C14", loc: "Kitchen", round: 1, text: "Muddy paw prints cross the kitchen floor, from the mudroom door to the back stairs. None lead toward the Great Room." },
    { id: "C15", loc: "Kitchen", round: 1, text: "From the kitchen sink you can see the back door through the window, but not the far end of the porch by the study." },
    { id: "C16", loc: "Dining Room", round: 1, text: "Edgar's place card. On the back, in his writing: \"Tonight, everyone gets what they deserve. -E\"" },
    { id: "C17", loc: "Dining Room", round: 1, opt: "ORB", text: "Taped under the seance table: a small Bluetooth speaker. A cue sheet next to it: \"3rd knock: play WAIL_02.\"" },
    { id: "C18", loc: "Dining Room", round: 1, opt: "ORB", text: "Madame Oriel's business card. Tucked behind it, an old staff badge: \"Doreen Fisk, Assistant to E. Thorne, 2014-2019.\"" },
    { id: "C19", loc: "Back Porch", round: 1, text: "The porch ashtray holds exactly one cigarette butt." },
    { id: "C20", loc: "Back Porch", round: 1, text: "Muddy paw prints run along the porch, from the back door to the study's French doors, and back again." },
    { id: "C21", loc: "Back Porch", round: 1, opt: "BOO", text: "Small sneaker prints in the mud under the study window." },
    { id: "C22", loc: "Mudroom", round: 1, text: "The breaker box. Every switch is still ON. Ruth's flashlight sits on the shelf beside it." },
    { id: "C23", loc: "Mudroom", round: 1, text: "A generator log on a clipboard: \"Started 11:28 PM - R.K.\"" },
    { id: "C24", loc: "Umbrella Stand", round: 2, item: true, text: "THE MANUSCRIPT. The Last Chapter by Edgar Thorne. Chapter 13 has been torn out. The margins are full of handwritten notes and rewrites, and the handwriting isn't Edgar's." },
    { id: "C25", loc: "Umbrella Stand", round: 2, text: "Wrapped in a wet towel: the Golden Raven award. A few coarse gray hairs are stuck in its base." },
    { id: "C26", loc: "Edgar's Safe", round: 2, text: "A letter from Edgar to Marcus Reed: \"The audit is done. $340,000 is missing. Confess to everyone by midnight, or I read Chapter 13 aloud and call my lawyer.\"" },
    { id: "C27", loc: "Edgar's Safe", round: 2, text: "Edgar's new will, signed last month: \"Hollowpine Lodge goes to Ruth Kowalski. To my nephew Julian, my library card and my forgiveness.\"" },
    { id: "C28", loc: "Edgar's Safe", round: 2, item: true, text: "THE 1998 PHOTO. Young Edgar and young Ruth by the lake, arm in arm. On the back: \"Summer '98, my muse.\"" },
    { id: "C29", loc: "Guest Rooms", round: 2, text: "Marcus's bag: a pair of rubber werewolf paw feet, caked in wet mud. Under them, spreadsheet printouts with whole columns cut out." },
    { id: "C30", loc: "Guest Rooms", round: 2, text: "Julian's bag: an IOU for $28,000 to \"Lucky Lou\", due November 1. Also $500 cash in a money clip engraved \"E.T.\"" },
    { id: "C31", loc: "Guest Rooms", round: 2, text: "Vivian's bag: a co-author contract for The Last Chapter. Vivian has signed it. Edgar hasn't." },
    { id: "C32", loc: "Guest Rooms", round: 2, opt: "ROT", text: "Graham's bag: a yellowed manuscript, The Hollow Girl by Graham Pike, 1996, with a publisher's rejection letter." },
    { id: "C33", loc: "Guest Rooms", round: 2, opt: "BOO", text: "Penny's camera. The last photo, stamped 10:22 PM, shows Edgar alive at his desk, typing, taken through the study window." },
    { id: "C34", loc: "Ruth's Cabin", round: 2, text: "Ruth's rubber boots by the door, size 7, still muddy. Ordinary boot treads." },
    { id: "C35", loc: "Ruth's Cabin", round: 2, text: "A letter on Ruth's table, from Edgar: \"The lodge is yours when I'm gone. Don't tell Julian.\"" },
    { id: "C36", loc: "Ruth's Cabin", round: 2, text: "A box of candles, half empty." }
  ],

  envelopes: [
    { loc: "Edgar's Safe", how: "Open after the group solves Puzzle 1 (The Safe)" },
    { loc: "Guest Rooms", how: "Open after the group solves Puzzle 2 (The Burnt Page)" },
    { loc: "Umbrella Stand", how: "Open after the group solves Puzzle 3 (The Route)" },
    { loc: "Ruth's Cabin", how: "Open when Round 2 starts" }
  ],

  seance: "\"My clock lies... the beast came early... it came in from the rain.\"",

  reveal: "The scream at 11:20 was a recording. Edgar was already dead. At 10:42, a werewolf walked out the back door for a cigarette he smoked once. He went along the porch, through the study's French doors, and struck Edgar from behind with his own award. He burned Chapter 13, set the recorder, wound the watch to 11:20 and smashed it. On the way back he hid the award and the manuscript in the umbrella stand, kicked off his muddy paws upstairs, and came down to make sure everyone was holding his arm when the scream came. The werewolf counted the gold twice and kept it once. Marcus Reed, you're under arrest."
};
