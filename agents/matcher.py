PROFILE = {

    "skills": {

        "python",

        "research",

        "writing",

        "git",

        "project management",

        "documentation"

    }

}


class JobMatcher:

    def score(self, job):

        matches = 0

        for skill in job["skills"]:

            if skill.lower() in PROFILE["skills"]:

                matches += 1

        return int(matches / len(job["skills"]) * 100)


    def rank_jobs(self, jobs):

        for job in jobs:

            job["score"] = self.score(job)

        jobs.sort(

            key=lambda x: x["score"],

            reverse=True

        )

        return jobs
