import { Injectable } from '@angular/core';
import { ParserRegister } from '.';
import { BibliographyClass, BibliographyInfo, XMLElement } from '../../models/evt-models';

@Injectable({
  providedIn: 'root',
})
export class BibliographicEntriesParserService {
  private tagName = `.${BibliographyClass}`;
  private parserName = 'evt-bibliographic-entry-parser';
  public parseAnaloguesEntries(document: XMLElement) {
    const bibliographicParser = ParserRegister.get(this.parserName);

    return Array.from(document.querySelectorAll<XMLElement>(this.tagName))
    .map((bib) => bibliographicParser.parse(bib));
  }

  parseBibliographicEntries(xml: XMLElement) {
    const biblParser = ParserRegister.get(this.parserName);

    return {
      type: BibliographyInfo,
      bibliographicEntries: Array.from(xml.querySelectorAll<XMLElement>('bibl')).map((s) => biblParser.parse(s))
      .concat(Array.from(xml.querySelectorAll<XMLElement>('biblStruct')).map((s) => biblParser.parse(s))),
    }
  }
}

