from music21 import *
import logging
from typing import List, Dict, Optional, Union
from .error_types import HarmonyError
from .visualization import generate_visualization
from .report_generator import ReportGenerator
from .utils import categorize_errors_by_severity, identify_common_problems

logger = logging.getLogger(__name__)


class HarmonyAnalyzer:
    """
    Analyzes musical scores for harmony errors and generates reports.

    Attributes:
        score: The loaded music21 score
        errors: List of detected harmony errors
        visualization_path: Path to the generated score visualization
        key: Detected key of the piece
    """

    def __init__(self):
        self.score = None
        self.errors: List[HarmonyError] = []
        self.visualization_path = None
        self.key = None

    def load_score(self, musicxml_path: str) -> None:
        """Loads a score from MusicXML file and determines the key"""
        try:
            self.score = converter.parse(musicxml_path)
            # Determine the key of the piece
            self.key = self.score.analyze('key')
            logger.debug(
                f"Successfully loaded score from {musicxml_path} in key {self.key}"
            )
            self.visualization_path = generate_visualization(self.score)
        except Exception as e:
            logger.error(f"Error loading score: {str(e)}", exc_info=True)
            raise Exception(f"Failed to load score: {str(e)}")

    def analyze(self) -> List[HarmonyError]:
        """Performs complete analysis of the score"""
        try:
            self.errors = []  # Reset errors before new analysis

            if not self.validate_score():
                raise Exception("Invalid score - cannot perform analysis")

            self.check_parallel_fifths()
            self.check_parallel_octaves()
            self.check_voice_leading()
            self.check_chord_progressions()
            self.check_cadences()

            # Enhanced checks
            self.check_voice_spacing()
            self.check_hidden_fifths_octaves()
            self.check_voice_ranges()
            self.check_melodic_intervals()
            self.check_harmonic_rhythm()
            self.check_doubled_leading_tone()

            return self.errors
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            raise Exception(f"Analysis failed: {str(e)}")

    def check_parallel_fifths(self) -> None:
        """Checks for parallel fifths between voices"""
        if not self.score:
            return

        try:
            parts = self.score.parts
            if len(parts) < 2:
                return

            for part1_idx in range(len(parts) - 1):
                for part2_idx in range(part1_idx + 1, len(parts)):
                    notes1 = parts[part1_idx].flatten().notes
                    notes2 = parts[part2_idx].flatten().notes

                    for i in range(len(notes1) - 1):
                        try:
                            curr_interval = interval.Interval(
                                noteStart=notes1[i], noteEnd=notes2[i])
                            next_interval = interval.Interval(
                                noteStart=notes1[i + 1], noteEnd=notes2[i + 1])

                            if curr_interval.simpleName == 'P5' and next_interval.simpleName == 'P5':
                                motion1 = notes1[
                                    i + 1].pitch.ps - notes1[i].pitch.ps
                                motion2 = notes2[
                                    i + 1].pitch.ps - notes2[i].pitch.ps

                                if (motion1 * motion2) > 0:  # Similar motion
                                    self.errors.append(
                                        HarmonyError(
                                            type='Parallel Fifths',
                                            measure=notes1[i].measureNumber,
                                            description=
                                            f'Parallel fifth movement between voices {part1_idx + 1} and {part2_idx + 1}',
                                            severity='high',
                                            voice1=part1_idx + 1,
                                            voice2=part2_idx + 1))
                        except Exception as e:
                            logger.warning(
                                f"Error checking interval at position {i}: {str(e)}"
                            )
                            continue

        except Exception as e:
            logger.error(f"Error in parallel fifths check: {str(e)}",
                         exc_info=True)

    def check_parallel_octaves(self) -> None:
        """Checks for parallel octaves between voices"""
        if not self.score:
            return

        try:
            parts = self.score.parts
            if len(parts) < 2:
                return

            for part1_idx in range(len(parts) - 1):
                for part2_idx in range(part1_idx + 1, len(parts)):
                    notes1 = parts[part1_idx].flatten().notes
                    notes2 = parts[part2_idx].flatten().notes

                    for i in range(len(notes1) - 1):
                        try:
                            curr_interval = interval.Interval(
                                noteStart=notes1[i], noteEnd=notes2[i])
                            next_interval = interval.Interval(
                                noteStart=notes1[i + 1], noteEnd=notes2[i + 1])

                            if curr_interval.simpleName == 'P8' and next_interval.simpleName == 'P8':
                                motion1 = notes1[
                                    i + 1].pitch.ps - notes1[i].pitch.ps
                                motion2 = notes2[
                                    i + 1].pitch.ps - notes2[i].pitch.ps

                                if (motion1 * motion2) > 0:  # Similar motion
                                    self.errors.append(
                                        HarmonyError(
                                            type='Parallel Octaves',
                                            measure=notes1[i].measureNumber,
                                            description=
                                            f'Parallel octave movement between voices {part1_idx + 1} and {part2_idx + 1}',
                                            severity='high',
                                            voice1=part1_idx + 1,
                                            voice2=part2_idx + 1))
                        except Exception as e:
                            logger.warning(
                                f"Error checking interval at position {i}: {str(e)}"
                            )
                            continue

        except Exception as e:
            logger.error(f"Error in parallel octaves check: {str(e)}",
                         exc_info=True)

    def check_voice_leading(self) -> None:
        """Checks voice leading rules"""
        if not self.score:
            return

        try:
            parts = self.score.parts
            for part_idx, part in enumerate(parts):
                notes = part.flatten().notes
                consecutive_leaps = 0

                for i in range(len(notes) - 1):
                    try:
                        interval_obj = interval.Interval(noteStart=notes[i],
                                                         noteEnd=notes[i + 1])
                        interval_size = abs(interval_obj.semitones)

                        # Check for large leaps
                        if interval_size > 12:
                            self.errors.append(
                                HarmonyError(
                                    type='Large Leap',
                                    measure=notes[i].measureNumber,
                                    description=
                                    f'Large melodic leap of {interval_size} semitones in voice {part_idx + 1}',
                                    severity='medium',
                                    voice1=part_idx + 1))
                            consecutive_leaps += 1
                        elif interval_size > 4:  # Count as a leap if larger than a major third
                            consecutive_leaps += 1
                        else:
                            consecutive_leaps = 0

                        # Check for too many consecutive leaps
                        if consecutive_leaps > 2:
                            self.errors.append(
                                HarmonyError(
                                    type='Consecutive Leaps',
                                    measure=notes[i].measureNumber,
                                    description=
                                    f'Too many consecutive leaps in voice {part_idx + 1}',
                                    severity='medium',
                                    voice1=part_idx + 1))

                        # Check for voice crossing
                        if part_idx < len(parts) - 1:
                            lower_voice = parts[part_idx + 1].flatten().notes
                            if i < len(lower_voice):
                                if notes[i].pitch < lower_voice[i].pitch:
                                    self.errors.append(
                                        HarmonyError(
                                            type='Voice Crossing',
                                            measure=notes[i].measureNumber,
                                            description=
                                            f'Voice {part_idx + 1} crosses below voice {part_idx + 2}',
                                            severity='medium',
                                            voice1=part_idx + 1,
                                            voice2=part_idx + 2))

                    except Exception as e:
                        logger.warning(
                            f"Error checking voice leading at position {i}: {str(e)}"
                        )
                        continue

        except Exception as e:
            logger.error(f"Error in voice leading check: {str(e)}",
                         exc_info=True)

    def check_chord_progressions(self) -> None:
        """Analyzes chord progressions"""
        if not self.score:
            return

        try:
            chordified = self.score.chordify()
            prev_chord = None
            prev_root = None

            for chord in chordified.recurse().getElementsByClass('Chord'):
                if prev_chord:
                    try:
                        curr_root = chord.root()

                        # Check for root position
                        if chord.inversion() != 0:
                            self.errors.append(
                                HarmonyError(
                                    type='Chord Position',
                                    measure=chord.measureNumber,
                                    description=
                                    f'Non-root position chord: {chord.commonName}',
                                    severity='low'))

                        if prev_root:
                            # Check for weak root progressions
                            interval_obj = interval.Interval(
                                noteStart=prev_root, noteEnd=curr_root)

                            # V-IV progression check
                            if (prev_root.name == 'G'
                                    and curr_root.name == 'F'):
                                self.errors.append(
                                    HarmonyError(
                                        type='Weak Progression',
                                        measure=chord.measureNumber,
                                        description=
                                        'V-IV progression (retrograde)',
                                        severity='medium'))

                            # Parallel root motion by fifth
                            if interval_obj.simpleName == 'P5':
                                self.errors.append(
                                    HarmonyError(
                                        type='Root Motion',
                                        measure=chord.measureNumber,
                                        description=
                                        'Parallel fifths in root motion',
                                        severity='low'))

                        prev_root = curr_root

                    except Exception as e:
                        logger.warning(
                            f"Error analyzing chord progression: {str(e)}")
                prev_chord = chord

        except Exception as e:
            logger.error(f"Error in chord progression check: {str(e)}",
                         exc_info=True)

    def check_cadences(self) -> None:
        """Verifies proper cadences"""
        if not self.score or not self.key:
            return

        try:
            chordified = self.score.chordify()
            chords = list(chordified.recurse().getElementsByClass('Chord'))

            if len(chords) >= 2:
                final_chords = chords[-2:]
                try:
                    # Get the chord roots
                    penultimate_root = final_chords[0].root()
                    final_root = final_chords[1].root()

                    # Analyze cadence type
                    if penultimate_root.name == 'G' and final_root.name == 'C':  # V-I
                        if final_chords[1].inversion() != 0:
                            self.errors.append(
                                HarmonyError(
                                    type='Cadence',
                                    measure=final_chords[1].measureNumber,
                                    description=
                                    'Final chord not in root position',
                                    severity='high'))
                    elif penultimate_root.name == 'F' and final_root.name == 'C':  # IV-I
                        self.errors.append(
                            HarmonyError(
                                type='Cadence',
                                measure=final_chords[1].measureNumber,
                                description=
                                'Plagal cadence - consider authentic cadence instead',
                                severity='medium'))
                    else:
                        self.errors.append(
                            HarmonyError(
                                type='Cadence',
                                measure=final_chords[1].measureNumber,
                                description='Non-standard final cadence',
                                severity='high'))

                except Exception as e:
                    logger.warning(f"Error analyzing cadence: {str(e)}")

        except Exception as e:
            logger.error(f"Error in cadence check: {str(e)}", exc_info=True)

    def check_voice_spacing(self) -> None:
        """Checks for proper spacing between voices"""
        if not self.score:
            return

        try:
            parts = self.score.parts
            for measure_number in range(1,
                                        len(self.score.measures(0, None)) + 1):
                measure_range = f'{measure_number}/{measure_number}'

                for part1_idx in range(len(parts) - 1):
                    for part2_idx in range(part1_idx + 1, len(parts)):
                        notes1 = parts[part1_idx].measures(
                            measure_range).flatten().notes
                        notes2 = parts[part2_idx].flatten().notes

                        for note1, note2 in zip(notes1, notes2):
                            interval_obj = interval.Interval(noteStart=note1,
                                                             noteEnd=note2)

                            # Check spacing between adjacent voices
                            if part1_idx < len(
                                    parts) - 2 and interval_obj.semitones > 12:
                                self.errors.append(
                                    HarmonyError(
                                        type='Voice Spacing',
                                        measure=measure_number,
                                        description=
                                        f'Excessive spacing between voices {part1_idx + 1} and {part2_idx + 1}',
                                        severity='medium',
                                        voice1=part1_idx + 1,
                                        voice2=part2_idx + 1))

                            # Check total spacing (shouldn't exceed 2 octaves except with bass)
                            if part1_idx == 0 and part2_idx == len(parts) - 1:
                                if interval_obj.semitones > 24:
                                    self.errors.append(
                                        HarmonyError(
                                            type='Voice Spacing',
                                            measure=measure_number,
                                            description=
                                            'Total voice spacing exceeds two octaves',
                                            severity='low',
                                            voice1=part1_idx + 1,
                                            voice2=part2_idx + 1))

        except Exception as e:
            logger.error(f"Error in voice spacing check: {str(e)}",
                         exc_info=True)

    def check_hidden_fifths_octaves(self) -> None:
        """Checks for hidden (direct) fifths and octaves between outer voices"""
        if not self.score:
            return

        try:
            soprano = self.score.parts[0].flatten().notes
            bass = self.score.parts[-1].flatten().notes

            for i in range(len(soprano) - 1):
                try:
                    curr_interval = interval.Interval(noteStart=soprano[i],
                                                      noteEnd=bass[i])
                    next_interval = interval.Interval(noteStart=soprano[i + 1],
                                                      noteEnd=bass[i + 1])

                    # Get motion direction
                    soprano_motion = soprano[i +
                                             1].pitch.ps - soprano[i].pitch.ps
                    bass_motion = bass[i + 1].pitch.ps - bass[i].pitch.ps

                    # Check for similar motion to perfect interval
                    if (soprano_motion * bass_motion > 0):  # Similar motion
                        if next_interval.simpleName in ['P5', 'P8']:
                            # Check if soprano moves by leap
                            if abs(soprano_motion) > 2:
                                self.errors.append(
                                    HarmonyError(
                                        type='Hidden Perfect Interval',
                                        measure=soprano[i].measureNumber,
                                        description=
                                        f'Hidden {next_interval.simpleName} between outer voices',
                                        severity='low',
                                        voice1=1,
                                        voice2=len(self.score.parts)))

                except Exception as e:
                    logger.warning(
                        f"Error checking hidden fifths/octaves at position {i}: {str(e)}"
                    )
                    continue

        except Exception as e:
            logger.error(f"Error in hidden fifths/octaves check: {str(e)}",
                         exc_info=True)

    # analyzer.py - Add this method to your HarmonyAnalyzer class
    def validate_score(self) -> bool:
        """Validates that the score is properly formatted"""
        try:
            if not self.score:
                logger.error("No score loaded")
                return False

            if not self.score.parts:
                logger.error("Score contains no parts")
                return False

            if len(self.score.parts) < 2:
                logger.error("Score must contain at least two voices")
                return False

            for part_idx, part in enumerate(self.score.parts):
                if not part.flatten().notes:
                    logger.error(f"Part {part_idx + 1} contains no notes")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating score: {str(e)}")
            return False

    def check_voice_ranges(self) -> None:
        """Checks if voices stay within their traditional ranges"""
        if not self.score:
            return

        # Define traditional vocal ranges (MIDI pitch numbers)
        ranges = {
            'Soprano': (60, 79),  # C4 to G5
            'Alto': (55, 74),  # G3 to D5
            'Tenor': (48, 67),  # C3 to G4
            'Bass': (40, 60)  # E2 to C4
        }

        try:
            parts = self.score.parts
            voice_types = ['Soprano', 'Alto', 'Tenor', 'Bass']

            for part_idx, part in enumerate(parts):
                if part_idx < len(voice_types):
                    voice_type = voice_types[part_idx]
                    min_pitch, max_pitch = ranges[voice_type]

                    for note in part.flatten().notes:
                        pitch_num = note.pitch.midi

                        if pitch_num < min_pitch:
                            self.errors.append(
                                HarmonyError(
                                    type='Voice Range',
                                    measure=note.measureNumber,
                                    description=
                                    f'{voice_type} voice below traditional range',
                                    severity='medium',
                                    voice1=part_idx + 1))

                        if pitch_num > max_pitch:
                            self.errors.append(
                                HarmonyError(
                                    type='Voice Range',
                                    measure=note.measureNumber,
                                    description=
                                    f'{voice_type} voice above traditional range',
                                    severity='medium',
                                    voice1=part_idx + 1))

        except Exception as e:
            logger.error(f"Error in voice range check: {str(e)}",
                         exc_info=True)

    def check_melodic_intervals(self) -> None:
        """Checks for problematic melodic intervals"""
        if not self.score:
            return

        try:
            for part_idx, part in enumerate(self.score.parts):
                notes = part.flatten().notes

                for i in range(len(notes) - 1):
                    try:
                        interval_obj = interval.Interval(noteStart=notes[i],
                                                         noteEnd=notes[i + 1])

                        # Check for augmented intervals
                        if interval_obj.isAugmented:
                            self.errors.append(
                                HarmonyError(
                                    type='Melodic Interval',
                                    measure=notes[i].measureNumber,
                                    description=
                                    f'Augmented interval in voice {part_idx + 1}',
                                    severity='high',
                                    voice1=part_idx + 1))

                        # Check for difficult intervals
                        if interval_obj.simpleName in ['M7', 'd5', 'A4']:
                            self.errors.append(
                                HarmonyError(
                                    type='Melodic Interval',
                                    measure=notes[i].measureNumber,
                                    description=
                                    f'Difficult melodic interval ({interval_obj.simpleName}) in voice {part_idx + 1}',
                                    severity='medium',
                                    voice1=part_idx + 1))

                    except Exception as e:
                        logger.warning(
                            f"Error checking melodic interval at position {i}: {str(e)}"
                        )
                        continue

        except Exception as e:
            logger.error(f"Error in melodic interval check: {str(e)}",
                         exc_info=True)

    def check_doubled_leading_tone(self) -> None:
        """Checks for doubled leading tones"""
        if not self.score or not self.key:
            return

        try:
            leading_tone = self.key.asKey().getLeadingTone()

            for measure_number in range(1,
                                        len(self.score.measures(0, None)) + 1):
                measure_range = f'{measure_number}/{measure_number}'

                # Get all notes in the current measure
                measure_notes = []
                for part in self.score.parts:
                    measure_notes.extend(
                        part.measures(measure_range).flatten().notes)

                # Count leading tones
                leading_tone_count = sum(
                    1 for note in measure_notes
                    if note.pitch.name == leading_tone.name)

                if leading_tone_count > 1:
                    self.errors.append(
                        HarmonyError(type='Doubled Leading Tone',
                                     measure=measure_number,
                                     description=
                                     'Leading tone appears in multiple voices',
                                     severity='high'))

        except Exception as e:
            logger.error(f"Error in doubled leading tone check: {str(e)}",
                         exc_info=True)

    def check_harmonic_rhythm(self) -> None:
        """Analyzes the harmonic rhythm for potential issues"""
        if not self.score:
            return

        try:
            chordified = self.score.chordify()
            prev_chord = None
            rapid_changes = 0
            same_chord_count = 0

            for chord in chordified.recurse().getElementsByClass('Chord'):
                if prev_chord:
                    # Check for very rapid chord changes
                    if chord.offset - prev_chord.offset < 1.0:  # Less than a quarter note
                        rapid_changes += 1
                        if rapid_changes > 3:  # More than 3 rapid changes in succession
                            self.errors.append(
                                HarmonyError(
                                    type='Harmonic Rhythm',
                                    measure=chord.measureNumber,
                                    description='Too many rapid chord changes',
                                    severity='low'))
                    else:
                        rapid_changes = 0

                    # Check for static harmony
                    if prev_chord.pitches == chord.pitches:
                        same_chord_count += 1
                        if same_chord_count > 4:  # Same chord for more than 4 beats
                            self.errors.append(
                                HarmonyError(
                                    type='Harmonic Rhythm',
                                    measure=chord.measureNumber,
                                    description='Static harmony for too long',
                                    severity='low'))
                    else:
                        same_chord_count = 0

                prev_chord = chord

        except Exception as e:
            logger.error(f"Error in harmonic rhythm check: {str(e)}",
                         exc_info=True)

    def validate_score(self) -> bool:
        """Validates that the score is properly formatted"""
        try:
            if not self.score:
                logger.error("No score loaded")
                return False

            if not self.score.parts:
                logger.error("Score contains no parts")
                return False

            if len(self.score.parts) < 2:
                logger.error("Score must contain at least two voices")
                return False

            for part_idx, part in enumerate(self.score.parts):
                if not part.flatten().notes:
                    logger.error(f"Part {part_idx + 1} contains no notes")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating score: {str(e)}")
            return False

    def clear(self) -> None:
        """Resets the analyzer state"""
        self.score = None
        self.errors = []
        self.visualization_path = None
        self.key = None

    def generate_report(self) -> Dict:
        """Generates analysis report with statistics"""
        return {
            'total_errors': len(self.errors),
            'errors_by_severity': {
                'high': sum(1 for e in self.errors if e.severity == 'high'),
                'medium':
                sum(1 for e in self.errors if e.severity == 'medium'),
                'low': sum(1 for e in self.errors if e.severity == 'low')
            },
            'statistics': {
                'measures_analyzed':
                len(self.score.measures(0, None)) if self.score else 0,
                'key':
                str(self.key) if self.key else 'Unknown',
                'total_voices':
                len(self.score.parts) if self.score else 0
            }
        }
