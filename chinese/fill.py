# Copyright © 2013 Chris Hatch <foonugget@gmail.com>
# Copyright © 2014 Thomas TEMPÉ <thomas.tempe@alysse.org>
# Copyright © 2017-2018 Joseph Lorimer <luoliyan@posteo.net>
#
# This file is part of Chinese Support Redux.
#
# Chinese Support Redux is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Chinese Support Redux is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Chinese Support Redux.  If not, see <https://www.gnu.org/licenses/>.

from time import sleep

from anki.find import Finder
from aqt import mw
from aqt.utils import showInfo, askUser

from .behavior import (
    fill_all_definitions,
    update_Cantonese_fields,
    update_PinyinTW_fields,
    update_Pinyin_fields,
    update_Silhouette_fields,
    update_Simplified_fields,
    update_Traditional_fields,
    update_Transcription_fields,
    update_all_Color_fields,
    update_all_Ruby_fields,
    update_all_Sound_fields,
    update_bopomofo,
    update_example
)
from .main import config
from .util import cleanup, get_first, has_field, no_html


def fill_sounds():
    prompt = '''
    <div>This will update the <i>Sound</i> fields in the current
    deck, if they exist and are empty, using the selected speech
    engine.</div>
    <div>Please back-up your Anki deck first!</div>
    <div>(Please also note that there will be a 5 second delay
    between each sound request, to reduce burden on the server.
    This may therefore take a while.)</div>
    <div><b>Continue?</b></div>
    '''

    if not askUser(prompt):
        return

    query_str = 'deck:current'
    d_scanned = 0
    d_has_fields = 0
    d_already_had_sound = 0
    d_success = 0
    d_failed = 0

    notes = Finder(mw.col).findNotes(query_str)
    mw.progress.start(immediate=True, min=0, max=len(notes))
    for noteId in notes:
        d_scanned += 1
        note = mw.col.getNote(noteId)
        note_dict = dict(note)

        _hf_s = has_field(config['fields']['sound'], note_dict)
        _hf_sm = has_field(config['fields']['mandarinSound'], note_dict)
        _hf_sc = has_field(config['fields']['cantoneseSound'], note_dict)

        if (_hf_s or _hf_sm or _hf_sc) and has_field(config['fields']['hanzi'], note_dict):
            d_has_fields += 1

            hanzi = get_first(config['fields']['hanzi'], note_dict)

            if (get_first(config['fields']['sound'], note_dict) or
                    get_first(config['fields']['mandarinSound'], note_dict) or
                    get_first(config['fields']['cantoneseSound'], note_dict)):
                d_already_had_sound += 1
            else:
                msg = '''
                <b>Processing:</b> %(hanzi)s<br>
                <b>Updated:</b> %(d_success)d notes<br>
                <b>Failed:</b> %(d_failed)d notes''' % {
                    'hanzi': sanitize_hanzi(note_dict),
                    'd_success': d_success,
                    'd_failed': d_failed
                }
                mw.progress.update(label=msg, value=d_scanned)
                s, f = update_all_Sound_fields(hanzi, note_dict)
                d_success += s
                d_failed += f

                # write back to note from dict and flush
                fields = (
                    config['fields']['sound'] +
                    config['fields']['mandarinSound'] +
                    config['fields']['cantoneseSound']
                )
                for f in fields:
                    if f in note_dict and note_dict[f] != note[f]:
                        note[f] = note_dict[f]
                note.flush()
                sleep(5)

    mw.progress.finish()
    msg = '''
%(d_success)d new pronunciations downloaded

%(d_failed)d downloads failed

%(have)d/%(d_has_fields)d notes now have pronunciation''' % {
    'd_success': d_success,
    'd_failed': d_failed,
    'have': d_already_had_sound+d_success,
    'd_has_fields': d_has_fields
}
    if d_failed > 0:
        msg += (
            'TTS is taken from an online source. '
            'It may not always be fully responsive. '
            'Please check your network connexion, or retry later.'
        )
    showInfo(msg)


def fill_pinyin():
    prompt = '''
    <div>This will update the <i>Pinyin</i> (or <i>Transcription</i>),
    <i>Color</i> and <i>Ruby</i> fields in the current deck, if they exist.</div>
    <div><i>Pinyin</i> and <i>Transcription</i> will be filled if empty.
    Otherwise, their colorization and accentuation will be refreshed as needed.</div>
    <div>Please back-up your Anki deck first!</div>
    <div><b>Continue?</b></div>
    '''

    if not askUser(prompt):
        return

    query_str = 'deck:current'
    d_scanned = 0
    d_has_fields = 0
    d_added_pinyin = 0
    d_updated = 0

    notes = Finder(mw.col).findNotes(query_str)
    mw.progress.start(immediate=True, min=0, max=len(notes))
    for noteId in notes:
        d_scanned += 1
        note = mw.col.getNote(noteId)
        note_dict = dict(note)

        _hf_t = has_field(config['fields']['transcription'], note_dict)
        _hf_py = has_field(config['fields']['pinyin'], note_dict)
        _hf_pytw = has_field(config['fields']['pinyinTaiwan'], note_dict)
        _hf_cant = has_field(config['fields']['cantonese'], note_dict)
        _hf_bpmf = has_field(config['fields']['bopomofo'], note_dict)

        if ((_hf_t or _hf_py or _hf_pytw or _hf_cant or _hf_bpmf) and
                has_field(config['fields']['hanzi'], note_dict)):
            d_has_fields += 1

            msg = '''
            <b>Processing:</b> %(hanzi)s<br>
            <b>Filled pinyin:</b> %(pinyin)d notes<br>
            <b>Updated: </b>%(updated)d fields''' % {
                'hanzi': sanitize_hanzi(note_dict),
                'pinyin': d_added_pinyin,
                'updated': d_updated
            }
            mw.progress.update(label=msg, value=d_scanned)

            hanzi = get_first(config['fields']['hanzi'], note_dict)
            results = 0

            if _hf_t:
                results += update_Transcription_fields(hanzi, note_dict)
            if _hf_py:
                results += update_Pinyin_fields(hanzi, note_dict)
            if _hf_pytw:
                results += update_PinyinTW_fields(hanzi, note_dict)
            if _hf_cant:
                results += update_Cantonese_fields(hanzi, note_dict)
            if _hf_bpmf:
                results += update_bopomofo(hanzi, note_dict)

            if results != 0:
                d_added_pinyin += 1

            update_all_Color_fields(hanzi, note_dict)
            update_all_Ruby_fields(hanzi, note_dict)

            def write_back(fields):
                num_updated = 0
                for f in fields:
                    if f in note_dict and note_dict[f] != note[f]:
                        note[f] = note_dict[f]
                        num_updated += 1
                return num_updated

            d_updated += write_back(config['fields']['transcription'])
            d_updated += write_back(config['fields']['pinyin'])
            d_updated += write_back(config['fields']['pinyinTaiwan'])
            d_updated += write_back(config['fields']['cantonese'])
            d_updated += write_back(config['fields']['bopomofo'])
            d_updated += write_back(config['fields']['color'])
            d_updated += write_back(config['fields']['colorPinyin'])
            d_updated += write_back(config['fields']['colorPinyinTaiwan'])
            d_updated += write_back(config['fields']['colorCantonese'])
            d_updated += write_back(config['fields']['colorBopomofo'])
            d_updated += write_back(config['fields']['ruby'])
            d_updated += write_back(config['fields']['rubyPinyin'])
            d_updated += write_back(config['fields']['rubyPinyinTaiwan'])
            d_updated += write_back(config['fields']['rubyCantonese'])
            d_updated += write_back(config['fields']['rubyBopomofo'])
            note.flush()

    mw.progress.finish()
    msg = '''
    <b>Processing:</b> %(hanzi)s<br>
    <b>Filled pinyin:</b> %(pinyin)d notes<br>
    <b>Updated: </b>%(updated)d fields''' % {
        'hanzi': sanitize_hanzi(note_dict),
        'pinyin': d_added_pinyin,
        'updated': d_updated
    }
    showInfo(msg)


def fill_definitions():
    prompt = '''
    <div>This will update the <i>Meaning</i>, <i>Classifier</i>, and <i>Also
    Written</i> fields in the current deck, if they exist and are empty.</div>
    <div>Please back-up your Anki deck first!</div>
    <div><b>Continue?</b></div>
    '''

    if not askUser(prompt):
        return

    query_str = 'deck:current'
    d_scanned = 0
    d_has_fields = 0
    d_success = 0
    d_failed = 0
    failed_hanzi = []
    notes = Finder(mw.col).findNotes(query_str)
    mw.progress.start(immediate=True, min=0, max=len(notes))
    for noteId in notes:
        d_scanned += 1
        note = mw.col.getNote(noteId)
        note_dict = dict(note)

        _hf_m = has_field(config['fields']['meaning'], note_dict)
        _hf_e = has_field(config['fields']['english'], note_dict)
        _hf_g = has_field(config['fields']['german'], note_dict)
        _hf_f = has_field(config['fields']['french'], note_dict)

        if (_hf_m or _hf_e or _hf_g or _hf_f) and has_field(config['fields']['hanzi'], note_dict):
            d_has_fields += 1

            msg = '''
            <b>Processing:</b> %(hanzi)s<br>
            <b>Chinese notes:</b> %(has_fields)d<br>
            <b>Translated:</b> %(filled)d<br>
            <b>Failed:</b> %(failed)d''' % {
                'hanzi': sanitize_hanzi(note_dict),
                'has_fields': d_has_fields,
                'filled': d_success,
                'failed': d_failed
            }
            mw.progress.update(label=msg, value=d_scanned)

            hanzi = get_first(config['fields']['hanzi'], note_dict)
            empty = len(get_first(config['fields']['meaning'], note_dict))
            empty += len(get_first(config['fields']['english'], note_dict))
            empty += len(get_first(config['fields']['german'], note_dict))
            empty += len(get_first(config['fields']['french'], note_dict))

            if not empty:
                result = fill_all_definitions(hanzi, note_dict)

                if result:
                    d_success += 1
                else:
                    d_failed += 1
                    if d_failed < 20:
                        failed_hanzi += [sanitize_hanzi(note_dict)]

            def write_back(fields):
                for f in fields:
                    if f in note_dict and note_dict[f] != note[f]:
                        note[f] = note_dict[f]

            write_back(config['fields']['meaning'])
            write_back(config['fields']['english'])
            write_back(config['fields']['german'])
            write_back(config['fields']['french'])
            write_back(config['fields']['classifier'])
            write_back(config['fields']['alternative'])
            note.flush()

    msg = '''
    <b>Translation complete</b><br>
    <b>Chinese notes:</b> %(has_fields)d<br>
    <b>Translated:</b> %(filled)d<br>
    <b>Failed:</b> %(failed)d''' % {
        'has_fields': d_has_fields,
        'filled': d_success,
        'failed': d_failed
    }
    if d_failed > 0:
        msg += (
            '<div>Translation failures may come either from connection issues '
            "(if you're using an online translation service), or because some "
            'words are not it the dictionary (for local dictionaries).</div>'
            '<div>The following notes failed: ' + ', '.join(failed_hanzi) + '</div>'
        )
    mw.progress.finish()
    showInfo(msg)


def fill_simp_trad():
    prompt = '''
    <div>This will update the <i>Simplified</i> and <i>Traditional</i> fields
    in the current deck, if they exist and are empty.</div>
    <div>Please back-up your Anki deck first!</div>
    <div><b>Continue?</b></div>
    '''

    if not askUser(prompt):
        return

    query_str = 'deck:current'
    d_scanned = 0
    d_has_fields = 0
    d_success = 0
    notes = Finder(mw.col).findNotes(query_str)
    mw.progress.start(immediate=True, min=0, max=len(notes))
    for noteId in notes:
        d_scanned += 1
        note = mw.col.getNote(noteId)
        note_dict = dict(note)
        if ((has_field(config['fields']['simplified'], note_dict) or
             has_field(config['fields']['traditional'], note_dict)) and
                has_field(config['fields']['hanzi'], note_dict)):
            d_has_fields += 1

            msg = '''
            <b>Processing:</b> %(hanzi)s<br>
            <b>Updated:</b> %(filled)d''' % {
                'hanzi': sanitize_hanzi(note_dict),
                'filled': d_success
            }
            mw.progress.update(label=msg, value=d_scanned)

            # Update simplified/traditional fields
            # If it's the same, leave empty,
            # so as to make this feature unobtrusive to simplified chinese users
            hanzi = get_first(config['fields']['hanzi'], note_dict)

            update_Simplified_fields(hanzi, note_dict)
            update_Traditional_fields(hanzi, note_dict)

            # write back to note from dict and flush
            for f in config['fields']['traditional']:
                if f in note_dict and note_dict[f] != note[f]:
                    note[f] = note_dict[f]
                    d_success += 1
            for f in config['fields']['simplified']:
                if f in note_dict and note_dict[f] != note[f]:
                    note[f] = note_dict[f]
                    d_success += 1
            note.flush()

    msg = '''
    <b>Update complete!</b> %(hanzi)s<br>
    <b>Updated:</b> %(filled)d notes''' % {
        'hanzi': sanitize_hanzi(note_dict),
        'filled': d_success
    }
    mw.progress.finish()
    showInfo(msg)


def fill_silhouette():
    prompt = '''
    <div>This will update the <i>Silhouette</i> fields in the current deck.</div>
    <div>Please back-up your Anki deck first!</div>
    <div><b>Continue?</b></div>
    '''

    if not askUser(prompt):
        return

    query_str = 'deck:current'
    d_scanned = 0
    d_has_fields = 0
    d_success = 0
    notes = Finder(mw.col).findNotes(query_str)
    mw.progress.start(immediate=True, min=0, max=len(notes))
    for noteId in notes:
        d_scanned += 1
        note = mw.col.getNote(noteId)
        note_dict = dict(note)
        if has_field(config['fields']['silhouette'], note_dict):
            d_has_fields += 1
            msg = '''
            <b>Processing:</b> %(hanzi)s<br>
            <b>Updated:</b> %(filled)d''' % {
                'hanzi': sanitize_hanzi(note_dict),
                'filled': d_success
            }
            mw.progress.update(label=msg, value=d_scanned)
            hanzi = get_first(config['fields']['hanzi'], note_dict)
            update_Silhouette_fields(hanzi, note_dict)

            # write back to note from dict and flush
            for f in config['fields']['silhouette']:
                if f in note_dict and note_dict[f] != note[f]:
                    note[f] = note_dict[f]
                    d_success += 1
            note.flush()

    msg = '''
    <b>Update complete!</b> %(hanzi)s<br>
    <b>Updated:</b> %(filled)d notes''' % {
        'hanzi': sanitize_hanzi(note_dict),
        'filled': d_success
    }
    mw.progress.finish()
    showInfo(msg)


def sanitize_hanzi(note):
    return cleanup(no_html(get_first(config['fields']['hanzi'], note)))
