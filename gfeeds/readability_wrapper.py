# flake8: noqa

from readability.readability import *


# THIS IS A HUGE HACK!
# readability-lxml has a bug where for some reason non-block tags inside
# paragraphs are given their own paragraph, basically breaking the formatting
# apparently the bug is caused by the transform_misused_divs_into_paragraphs
# method, that I replaced with an empty one. I also needed the parser to
# care about the now not replaced divs, so I needed to copy the whole
# score_paragraphs method to also search among divs
#
# If you happen to know what's wrong, please fix it either here or, even
# better, upstream. I'm sick of this library, but I couldn't find replacements
# and the code is a mess I don't want to deal with. This hack is the result
# of days of hitting my head on the wall and being sick and tired of having
# to deal with it.
class RDoc(Document):
    def transform_misused_divs_into_paragraphs(self):
        pass

    def score_paragraphs(self):
        MIN_LEN = self.min_text_length
        candidates = {}
        ordered = []
        for elem in self.tags(self._html(), "p", "pre", "td", "div"):
            parent_node = elem.getparent()
            if parent_node is None:
                continue
            grand_parent_node = parent_node.getparent()

            inner_text = clean(elem.text_content() or "")
            inner_text_len = len(inner_text)

            # If this paragraph is less than 25 characters
            # don't even count it.
            if inner_text_len < MIN_LEN:
                continue

            if parent_node not in candidates:
                candidates[parent_node] = self.score_node(parent_node)
                ordered.append(parent_node)

            if grand_parent_node is not None and grand_parent_node not in\
                    candidates:
                candidates[grand_parent_node] = self.score_node(
                    grand_parent_node
                )
                ordered.append(grand_parent_node)

            content_score = 1
            content_score += len(inner_text.split(","))
            content_score += min((inner_text_len / 100), 3)
            # if elem not in candidates:
            #    candidates[elem] = self.score_node(elem)

            # WTF? candidates[elem]['content_score'] += content_score
            candidates[parent_node]["content_score"] += content_score
            if grand_parent_node is not None:
                candidates[grand_parent_node]["content_score"] +=\
                    content_score / 2.0

        # Scale the final candidates score based on link density. Good content
        # should have a relatively small link density (5% or less) and be
        # mostly unaffected by this operation.
        for elem in ordered:
            candidate = candidates[elem]
            ld = self.get_link_density(elem)
            score = candidate["content_score"]
            log.debug(
                "Branch %6.3f %s link density %.3f -> %6.3f"
                % (score, describe(elem), ld, score * (1 - ld))
            )
            candidate["content_score"] *= 1 - ld

        return candidates
