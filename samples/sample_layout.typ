// ===================
// Page & Text Settings
// ===================
#set page(
  width: 5.5in,
  height: 8.5in,
  // margin: (left: 0.8in, right: 0.3in, top: 0.3in, bottom: 0.3in)
  margin: .7in
)

#set text(size: 10pt)

#set par(
  justify: true,
  leading: 0.65em,
)

#set footnote(numbering: "*")

#show heading: it => underline(it)

// ===================
// Helper Functions
// ===================
#let accent-color = luma(180)

#let aside(body) = block(
  stroke: (left: 1pt + accent-color),
  inset: (left: 10pt, y: 4pt),
  body
)

#let response(leader, people) = aside[
  / Leader: #leader
  / People: #people
]

#let rubric(body) = place(
  left,
  dx: -0.6in,
  dy: 1pt,  // push into the left margin
  box(
    width: 0.5in,
    align(right, text(size: 8pt, style: "italic", fill: luma(100), body))
  )
)

#let leaders-footer(elders, staff) = {
  v(1fr)
  
  set text(size: 14pt)
  align(center)[Church Leaders]
  v(-0.8em)
  set text(size: 10pt)

  rect(
    stroke: 1pt + luma(120),
    inset: 4pt,
    [
      #table(
        columns: (auto, 1fr, auto, auto),
        row-gutter: -4pt,
        stroke: none,
        ..for i in range(calc.max(elders.len(), staff.len())) {
          let elder = if i < elders.len() { ([#elders.at(i)], [_Ruling Elder_]) } else { ([], []) }
          
          if i == 4 {
            // Row 5: merge last two columns
            (elder.at(0), elder.at(1), table.cell(colspan: 2)[deacons\@trinityreformedkirk.com])
          } else {
            let staff-member = if i < staff.len() { ([#staff.at(i).at(0)], [_#staff.at(i).at(1)_]) } else { ([], []) }
            (elder.at(0), elder.at(1), staff-member.at(0), staff-member.at(1))
          }
        }
      )
    ]
  )
}

// ===================
// Content
// ===================
#align(center)[
  #v(1.5in)
  #text(size: 22pt)[Order of Worship]
  #v(-.2in)
  #text(size: 16pt)[{{FORMATTED_DATE}}]
  #v(1in)
]


Stir up your power, O Lord, and with great might come among us; and,
because we are sorely hindered by our sins, let your bountiful grace and
mercy speedily help and deliver us; through Jesus Christ our Lord, to
whom, with you and the Holy Spirit, be honor and glory, now and for
ever. _Amen_

#v(1fr)
#align(center)[(logo)]

#pagebreak()
#set page(
  width: 5.5in,
  height: 8.5in,
  margin: (left: 0.8in, right: 0.5in, top: 0.3in, bottom: 0.3in)
)

= Call to Worship
#rubric[Stand]
#response[Grace, mercy, and peace to you, from God the Father, Son, and Holy Spirit.][_Thanks Be to God_]

Scripture: {{HYMNS.0}}

#response[Lift Up Your Hearts!][_We Lift them up to the Lord!_]

Prayer

{{HYMNS.1}}

#rubric[Sit]
Admission of New Members: The Matson Family, The Woomer Family

{{#if BAPTISMS}}
Household Baptisms: {{BAPTISMS}}

#rubric[Stand]
#aside[
  Child of God, for you Jesus Christ came to this earth, struggled and suffered; for your sake He crossed Gethsemane and went through the darkness of Calvary; for your sake He cried: "It is finished"; for your sake He died and for your sake He overcame death; indeed for your sake, beloved. And this is the good news of our salvation: We love God, for He loved us first.
]
{{/if}}

= Confession of Sin

#rubric[Sit]
Exhortation

{{HYMNS.2}}

#rubric[Kneel]
Prayer of Confession: {{PRAYER_VERSE}}

#rubric[Stand]
Assurance of Pardon: {{ASSURANCE_VERSE}}

#response[Your sins are forgiven through Christ][Thanks be to God!]

Confess our Faith – Nicene Creed

#aside[
I believe in one God, the Father Almighty, Maker of heaven and earth, and of all things visible and invisible.

And in one Lord Jesus Christ, the only-begotten Son of God, begotten of the Father before all worlds, God of God, Light of Light, very God of very God, begotten, not made, being of one substance with the Father; by whom all things were made; who, for us men, and for our salvation, came down from Heaven, and was incarnate by the Holy Ghost of the virgin, Mary, and was made man; and was crucified also for us under Pontius Pilate; He suffered and was buried; and the third day He rose again, according to the Scriptures; and ascended into Heaven, and sits on the right hand of the Father; and He shall come again, with glory, to judge both the living and the dead; whose kingdom shall have no end.

And I believe in the Holy Ghost, the Lord, and Giver of Life, who proceeds from the Father and the Son; who with the Father and the Son together is worshiped and glorified; who spoke by the Prophets.

And I believe in one holy catholic and apostolic Church; I acknowledge one baptism for the remission of sins; and I look for the resurrection of the dead, and the life of the world to come.

Amen.
]

{{HYMNS.3}}

= Consecration

Scripture Reading
/ Old Testament: {{OT_READING}}
/ New Testament: {{NT_READING}}

#response[The Word of the Lord][Thanks be to God!]

#rubric[Sit]
Corporate Prayer

#rubric[Stand]
{{HYMNS.4}}

#rubric[Sit]
Sermon (Psalm 133) – Jason Cherry

#rubric[Stand]
{{HYMNS.5}}

Prayer for Offerings

The Lord's Prayer

#aside[
Our Father, who art in heaven, hallowed be thy name,
thy kingdom come, thy will be done, on earth as it is in heaven.
Give us this day our daily bread.
And forgive us our debts, as we forgive our debtors.
And lead us not into temptation, but deliver us from evil.
For thine is the kingdom, and the power, and the glory, forever.
Amen.
]

#pagebreak()
= Communion
#text(size: 8pt)[_Notes for Communion_
#footnote[
For those who are unable to partake of the wine, we also offer grape juice in the center of each tray and in an extra tray at the back. Gluten-free bread is also offered in the back. Feel free to pick these up while they are being distributed or beforehand.
]]

#rubric[Sit]Communion Homily

#response[Welcome to the Table of the Lord!][Thanks be to God!]

{{HYMNS.6}}

#rubric[Stand and Lift Hands]
{{HYMNS.7}}

= Commissioning

Charge & Benediction

{{BENEDICTION_SCRIPTURE}}

// ===================
// Footer
// ===================
#leaders-footer(
  ("Jason Cherry", "Daron Drown", "David Francis", "Larson Hicks", "Daniel Valcárcel"),
  (
    ("Brian McLain", "Pastor"),
    ("Gage Crowder", "Assistant Pastor"),
    ("Stewart Jordan", "Pastor-in-Residence"),
  )
)
