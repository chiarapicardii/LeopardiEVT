import { normalizeSpaces } from 'src/app/utils/xml-utils';
import { parse, xmlParser } from '.';
// eslint-disable-next-line max-len
import { AuthorDetail, BibliographicEntry, BibliographicList, BibliographicStructEntry, BibliographyClass, XMLElement } from '../../models/evt-models';
import { AttributeParser, GenericElemParser } from './basic-parsers';
import { createParser, getID, parseChildren, Parser } from './parser-models';
import { BasicParser } from './quotes-parser';

@xmlParser('listBibl', BibliographyParser)
@xmlParser('biblStruct', BibliographyParser)
@xmlParser('bibl', BibliographyParser)
@xmlParser('evt-bibliographic-entry-parser', BibliographyParser)
export class BibliographyParser extends BasicParser implements Parser<XMLElement> {
    protected attributeParser = createParser(AttributeParser, this.genericParse);
    protected elementParser = createParser(GenericElemParser, parse);

    protected getTrimmedText = function(s: Element): string {
        return s.textContent.replace(/[\n\r]+|[\s]{2,}/g, ' ').trim();
    }

    protected getChildrenTextByName = function(xml : XMLElement, name : string): string[] {
        return Array.from(xml.querySelectorAll<XMLElement>(name)).map((x) => this.getTrimmedText(x));
    }

    protected getChildrenByNameOnFirstLevelOnly = function(xml : XMLElement, name : string) {
        return Array.from(xml.querySelectorAll<XMLElement>(':scope > '+name)).map((x) => this.getTrimmedText(x));
    }

    protected getChildrenTextAndSpecificAttribute = function(xml: XMLElement, name: string, attribute: string): string[] {
        return Array.from(xml.querySelectorAll<XMLElement>(name)).map((x) =>
        x.getAttribute(attribute) !== null ?
        x.getAttribute(attribute)+' '+this.getTrimmedText(x) :
        this.getTrimmedText(x));
    }

    protected getQuoteElementText(element: XMLElement): string {
        const target = (element.parentNode['tagName'] === 'cit' || element.parentNode['tagName'] === 'note') ? element.parentNode : element;
        const quotes = Array.from(target.querySelectorAll<XMLElement>('quote'));
        if (quotes.length !== 0) {
            return normalizeSpaces(quotes[0].textContent);
        }

        return null;
    }

    protected getTitle(element: XMLElement): string {
        const titles = this.getChildrenTextByName(element, 'title');
        let title = '';
        if(titles.length > 0){
            title = titles.shift();
            titles.forEach((el) => { title = title.replace(el, `"${el}"`); });
        }

        return title;
    }

    protected getCitingText(element: XMLElement, includeUnit: boolean): string{
        const from = element.getAttribute('from');
        const to = element.getAttribute('to');
        const unit = element.getAttribute('unit');
        let returnString = '';
        if(unit && includeUnit){
            returnString = unit + ' ';
        }

        if(element.textContent === '' && !element.hasChildNodes()){
            if(from){
                if(from === to){
                    returnString += from;
                }else{
                    returnString += to ? `${from}-${to}` : `${from}ff`;
                }
            }
        }else{
            returnString += this.getTrimmedText(element);
        }

        return returnString;
    }

    protected getCitingTags(element: XMLElement, name: string): string[] {
        return Array.from(element.querySelectorAll(name)).map((el: XMLElement) => this.getCitingText(el, true));
    }


    /**
     *
     * @param element the parent XML element where to search the bibliographic reference scope
     * @param pattern a substring to search in \@unit, as it does not have a standard value.
     * For example, to get a volume number the best approach would be to search for the "vol" substring.
     * @returns the text representation of the bibliographic scope, along with the unit name.
     */
    protected getBibliographicReferenceByUnitMatching(element: XMLElement, pattern: string): string{
        const biblScopeElement = element.querySelector<XMLElement>('biblScope[unit*="' + pattern + '"]')
        const citedRangeElement = element.querySelector<XMLElement>('citedRange[unit*="' + pattern + '"');
        if(biblScopeElement || citedRangeElement){
            return biblScopeElement ? this.getCitingText(biblScopeElement, false) : this.getCitingText(citedRangeElement, false);
        }

        return '';
    }

    protected getAuthorsDetails(element: XMLElement): AuthorDetail[]{
        const authors = Array.from(element.querySelectorAll('author'));

        return authors.map((el) => {
            const forename = this.getChildrenTextByName(el as XMLElement, 'forename').reduce((prev, f) => prev + prev ? ' ' : '' + f, '');

            return {
            fullName: this.getTrimmedText(el),
            forename,
            forenameInitials: forename.replace(/\B(\w+)/g, '.'),
            surname: this.getChildrenTextByName(el as XMLElement, 'surname').reduce((prev, s) => prev + prev ? ' ' : '' + s, ''),
            nameLink: this.getChildrenTextByName(el as XMLElement, 'nameLink'),
            }
        });
    }

    protected getIdnoTextByType(element: XMLElement, type: string): string{
        const idno = element.querySelector<XMLElement>('idno[type="' + type + '" i]');

        return idno ? this.getTrimmedText(idno) : null;
    }

    protected getDate(xml: XMLElement): string[]{
        return Array.from(xml.querySelectorAll('date'))
            .map((x) => x.getAttribute('when') && !x.textContent ? x.getAttribute('when') : this.getTrimmedText(x));
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    parse(xml: XMLElement): any {

        switch (xml.tagName) {
            case 'ref':
            case 'analytic':
            case 'series':
            case 'monogr':
            case 'bibl':
                return {
                    type: BibliographicEntry,
                    id: getID(xml),
                    class: BibliographyClass,
                    attributes: this.attributeParser.parse(xml),
                    title: this.getChildrenTextByName(xml, 'title'),
                    titleDetails: { title: this.getTitle(xml), level: xml.querySelector('title')?.getAttribute('level') },
                    publication: this.getTitle(xml),
                    idno: this.getChildrenTextByName(xml, 'idno'),
                    doi: this.getIdnoTextByType(xml, 'DOI'),
                    author: this.getChildrenTextByName(xml,'author'),
                    authorsDetails: this.getAuthorsDetails(xml),
                    editor: this.getChildrenTextByName(xml,'editor'),
                    date: this.getDate(xml),
                    publisher: this.getChildrenTextByName(xml,'publisher'),
                    pubPlace: this.getChildrenTextByName(xml,'pubPlace'),
                    citedRange: this.getCitingTags(xml, 'citedRange'),
                    biblScope: this.getCitingTags(xml, 'biblScope'),
                    pageNumber: this.getBibliographicReferenceByUnitMatching(xml, 'page'),
                    volumeNumber: this.getBibliographicReferenceByUnitMatching(xml, 'vol'),
                    issueNumber: this.getBibliographicReferenceByUnitMatching(xml, 'iss'),
                    content: parseChildren(xml, this.genericParse),
                    text: xml.textContent,
                    quotedText: this.getQuoteElementText(xml),
                    isInsideCit: (xml.parentNode['tagName'] === 'cit' || xml.parentNode['tagName'] === 'note'),
                    originalEncoding: xml,
                };
            case 'cit':
            case 'listBibl':
            case 'note':
                return {
                    type: BibliographicList,
                    id: getID(xml),
                    attributes: this.attributeParser.parse(xml),
                    head: Array.from(xml.querySelectorAll<XMLElement>('head')).map((x) => x.textContent),
                    sources: Array.from(xml.querySelectorAll<XMLElement>('bibl')).map((x) => this.parse(x)),
                    content: parseChildren(xml, this.genericParse),
                };
            case 'biblStruct':
                return {
                    type: BibliographicStructEntry,
                    id: getID(xml),
                    attributes: this.attributeParser.parse(xml),
                    analytic: Array.from(xml.querySelectorAll<XMLElement>('analytic')).map((x) => this.parse(x)),
                    monogrs: Array.from(xml.querySelectorAll<XMLElement>('monogr')).map((x) => this.parse(x)),
                    series: Array.from(xml.querySelectorAll<XMLElement>('series')).map((x) => this.parse(x)),
                    content: parseChildren(xml, this.genericParse),
                    originalEncoding: xml,
                };
            default:
                // it should never reach here but we don't want risking to not parse an element anyway...
                return this.elementParser.parse(xml)
        }
    }
}
