#import "config.typ": *

#show: show-theorion
#show: codly-init.with()
#show: metropolis-theme.with(
  aspect-ratio: "16-9",
  footer: self => self.info.institution,
  navigation: "mini-slides",
	config-common(slide-level: 2),
  config-info(
    title: [HJudge],
    subtitle: [],
    author: [Đặng Xuân Minh Hiếu],
    date: datetime.today(),
    institution: [Uriel],
    logo: image("logo.jpg", height: 25%),
  ),
)


#title-slide()

= Outline <touying:hidden>

#outline(title: none, indent: 1em, depth: 2)


#include "p1.typ"
#include "p2.typ"
#include "p3.typ"
#include "p4.typ"
#include "p5.typ"
