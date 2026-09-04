let's remake the whole thing with a thorough step by step review, we moved everything to a _prevver folder and only resurface reviewed elementsthat is only a first version reference implementation you should consult me before anything is used and reused

we need four distinct part, built one by one
* we need a very thorough description document
* we need extensive representation tables
* we need a tool that allows the testing of the input system and its language specific ways on the web
* we need at least one reference implemetation as a true OS level input system

need to define unified names for things used like name of the notations



1. descripting document


cornerstones

- we want to comply with one keyboard on mobile using the minimal latin set as input while allow for a wide variety of languages to annotate their own phonetic/phonemic differences
- we want to build a universal phonemic set of points that are relatively small in number and easy to learn and represent smoothly with latin base characters and some extra acutes aiding multilingual people and language learners to use a single coherent writing system

the input should unambigously translate into the glyphs by using single chars and char+operator combinations in order to avoid any ambiguities in the input the 26 latin chars are separated into base and operator characters the combination of base and 0 or more operator characters give us the points in the system


as this is a phonemic system with the aim to cover many languages with the lowest viable number of points many points could not have a fix phonemic presentation

single chars and many widely used phonemes are having a fixed phonetic equivalent while not so ubiquitous phenomena could get a language specific colour to it, extra rare things get their own specific notation by language so we have 3 categories:
- fixed or narrow -- widely use chars, mostly base only but max base + 1 operator
- approx or  normal -- similar things that constitute minor differences that are almost never contrasted in any language
- exotic or wide -- things that are very specific to a given or few languages, usually used when something is contrasted within a language that would otherwise fit within one of the wider categories, thus this 3rd type of notation could vary significantly while still stays in at least the neighbourhood of it base point, should usually mean a systemic modifier like aspiration, velarisation or retroflex qualities

the notation could not follow all existing conventions as they are mostly language specific or annotate phonetic qualities which we both want to avoid being non language specific and phonemic

dialect and speech impediments are never recorded, but the exotic notaion might be used in these cases as it is quite rare otherwise, but no new notarion should be invented for these cases, very fine phonetic qualities should be the same way outside the notation as current notations exclude them our notation would still be significantly more expressive in the majority of cases

the notation is always follow the small letters characteristic for consonants -- letter that have something under the baseline receive acutes above others under

typical consonant notaion of the system is the undercomma that is both elongated and touches the base letter -- this is deliberately something not yet used widely so it could become a characteristic of the notation while also allows to have easy to distingwish handwriting qualities -- we need to name this type of annotation somehow, for now let's call it ???

other notations for consonants:
- single dot
- potentially double dot
- undercomma leaning the other way which once someone gets used to the normal way genuinly generates the rare/exotic/weird feeling

for the vowels we try to limit the notations to make a system that feels consistent acceptable acutes are the long, double dot, double long acute

we need to consider the exotic logic applied to the vowel system